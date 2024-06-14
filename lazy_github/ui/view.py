import lazy_github.lib.github as g
from datetime import datetime
from github.Repository import Repository
from github.PullRequest import PullRequest

from textual import log, work, on
from textual.reactive import reactive
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Footer,
    OptionList,
    Markdown,
    Log,
    Label,
    RichLog,
    TabbedContent,
    TabPane,
)
from textual.widgets.option_list import Option

# Color palletes
# https://coolors.co/84ffc9-aab2ff-eca0ff


def log_event(app: App, message: str) -> None:
    "Helper function for writing to the textual log and displayed command log"
    log(message)
    log_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    app.query_one("LazyGithubCommandLog").write_line(f"{log_time}: {message}")


class LazyGithubContainer(Container):
    """
    Base container class for focusible containers within the Lazy Github UI
    """

    DEFAULT_CSS = """
    LazyGithubContainer {
        display: block;
        border: solid #aab2ff;
    }

    LazyGithubContainer:focus-within {
        height: 40%;
        border: solid #84ffc9;
    }
    """


class LazyGithubOptionList(OptionList):
    "An option list for LazyGithub that provides some more vim-like bindings"

    BINDINGS = [("j", "cursor_down"), ("k", "cursor_up"), ("space", "select")]

    @work
    async def start_loading(self):
        self.clear_options()
        self.loading = True

    @work
    async def set_options(self, options: list[Option]):
        self.clear_options()
        self.add_options(options)
        self.loading = False


class ReposOptionsList(LazyGithubOptionList):
    pass


class SelectedRepoDisplay(Container):
    selected_repo: reactive[Repository | None] = None

    def compose(self) -> ComposeResult:
        yield Markdown(f"Selected repo: **{self.selected_repo.name}**")


class ReposContainer(LazyGithubContainer):
    BINDINGS = [
        ("f", "toggle_favorite_repo", "Toggle favorite"),
        ("enter", "select"),
    ]

    def compose(self) -> ComposeResult:
        self.border_title = "[1] Repositories"
        yield ReposOptionsList()

    @work(thread=True)
    def select_repo(self, repo_id):
        # Clear out the data lists below
        # TODO: These should really be updated to use async events in textual
        #   https://textual.textualize.io/guide/events/
        pr_options_list = self.app.query_one(PullRequestsOptionsList)
        self.app.call_from_thread(pr_options_list.start_loading)
        issues_options_list = self.app.query_one(IssuesOptionList)
        self.app.call_from_thread(issues_options_list.start_loading)
        action_options_list = self.app.query_one(ActionsOptionList)
        self.app.call_from_thread(action_options_list.start_loading)

        repo = g.github_client().get_repo(repo_id)
        log_event(self.app, f"Switching to repo: {repo.full_name}")

        # Update the selected PR at the top of the UI
        self.app.query_one(CurrentlySelectedRepo).current_repo = repo

        # Update the list of pull requests
        prs = repo.get_pulls()
        new_pr_options = [Option(f"#{pr.number}: {pr.title}", pr) for pr in prs]
        self.app.call_from_thread(lambda: pr_options_list.set_options(new_pr_options))

        # Update the list of issues
        issues = repo.get_issues(sort="created")
        new_issues_options = [Option(f"#{issue.number}: {issue.title}", issue) for issue in issues]
        self.app.call_from_thread(lambda: issues_options_list.set_options(new_issues_options))

        # Update the list of actions
        action_runs = repo.get_workflow_runs()
        new_action_options = [Option(f"#{action.run_number}: {action.name}", action.id) for action in action_runs]
        self.app.call_from_thread(lambda: action_options_list.set_options(new_action_options))

    async def action_toggle_favorite_repo(self):
        repo_list = self.query_one(ReposOptionsList)
        if highlighted_option := repo_list.highlighted:
            selected_repo_id = repo_list.get_option_at_index(highlighted_option).id
            repo = g.github_client().get_repo(selected_repo_id)
            log_event(self.app, f"Favoriting repo {repo.full_name}")

    @on(ReposOptionsList.OptionSelected)
    async def repo_selected(self, option: Option):
        self.select_repo(option.option_id)


class PullRequestsOptionsList(LazyGithubOptionList):
    pass


class PullRequestsContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[2] Pull Requests"
        yield PullRequestsOptionsList()

    @work()
    async def select_pull_request(self, pr: PullRequest) -> str:
        log_event(self.app, f"Selected PR {pr}")
        scratch_space = self.app.query_one(ScratchSpaceContainer)
        scratch_space.show_pr_details(pr)

    @on(PullRequestsOptionsList.OptionSelected)
    async def pr_selected(self, option: Option):
        self.select_pull_request(option.option_id)


class IssuesOptionList(LazyGithubOptionList):
    pass


class IssuesContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[3] Issues"
        yield IssuesOptionList()


class ActionsOptionList(LazyGithubOptionList):
    pass


class ActionsContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[4] Actions"
        yield ActionsOptionList()


class PrOverviewTabPane(TabPane):
    def __init__(self, pr: PullRequest) -> None:
        super().__init__("Overview", id="overview")
        self.pr = pr

    def compose(self) -> ComposeResult:
        yield Label(f"[b]Title[/b]: {self.pr.title}", id="pr_title")


class PrDiffTabPane(TabPane):
    def __init__(self, pr: PullRequest) -> None:
        super().__init__("Diff", id="diff_pane")
        self.pr = pr

    def compose(self) -> ComposeResult:
        yield RichLog(id="diff_contents")

    @work
    async def write_diff(self, diff: str) -> None:
        self.query_one("#diff_contents", RichLog).write(diff)

    @work(thread=True)
    def fetch_diff(self):
        diff = g.get_diff(self.pr)
        self.write_diff(diff)

    def on_mount(self) -> None:
        self.fetch_diff()


class PrConversationTabPane(TabPane):
    def __init__(self, pr: PullRequest) -> None:
        super().__init__("Conversation", id="conversation")
        self.pr = pr

    def compose(self) -> ComposeResult:
        yield Label("Conversation")


class ScratchSpaceContainer(LazyGithubContainer):
    DEFAULT_CSS = """
    ScratchSpaceContainer {
        height: 90%;
        dock: right;
    }
    ScratchSpaceContainer:focus-within {
        height: 80%;
    }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "[5] Scratch space"
        yield TabbedContent(id="scratch_space_tabs")

    def show_pr_details(self, pr: PullRequest) -> None:
        # Update the tabs to show the PR details
        tabbed_content: TabbedContent = self.query_one("#scratch_space_tabs")
        log(f"raw PR = {pr.raw_data}")
        tabbed_content.clear_panes()
        tabbed_content.add_pane(PrOverviewTabPane(pr))
        tabbed_content.add_pane(PrDiffTabPane(pr))
        tabbed_content.add_pane(PrConversationTabPane(pr))
        tabbed_content.focus()


class LazyGithubCommandLog(Log):
    pass


class CommandLogSection(LazyGithubContainer):
    DEFAULT_CSS = """
    CommandLogSection {
        height: 20%;
        dock: bottom;
    }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "[6] Command Log"
        yield LazyGithubCommandLog()


class SelectionsPane(Container):
    DEFAULT_CSS = """
    SelectionsPane {
        height: 100%;
        width: 40%;
        dock: left;
    }
    """

    def compose(self) -> ComposeResult:
        yield ReposContainer(id="repos")
        yield PullRequestsContainer(id="pull_requests")
        yield IssuesContainer(id="issues")
        yield ActionsContainer(id="actions")


class DetailsPane(Container):
    def compose(self) -> ComposeResult:
        yield ScratchSpaceContainer(id="Scratch")
        yield CommandLogSection()


class MainViewPane(Container):
    BINDINGS = [
        ("1", "focus_section('ReposOptionsList')"),
        ("2", "focus_section('PullRequestsOptionsList')"),
        ("3", "focus_section('IssuesOptionList')"),
        ("4", "focus_section('ActionsOptionList')"),
        ("5", "focus_section('#scratch_space_tabs')"),
        ("6", "focus_section('LazyGithubCommandLog')"),
    ]

    def action_focus_section(self, selector: str) -> None:
        self.query_one(selector).focus()

    def compose(self) -> ComposeResult:
        yield SelectionsPane()
        yield DetailsPane()


class CurrentlySelectedRepo(Widget):
    current_repo: reactive[Repository | None] = reactive(None)

    def render(self):
        if self.current_repo:
            return f"Current repo: [green]{self.current_repo.full_name}[/green]"
        else:
            return "No repository selected"


class LazyGithubHeader(Container):
    DEFAULT_CSS = """
    LazyGithubHeader {
        height: 10%;
        width: 100%;
        border: solid #ECA0FF;
    }
    """

    def compose(self):
        yield CurrentlySelectedRepo()


class LazyGithubFooter(Footer):
    pass


class LazyGithubMainScreen(Screen):
    BINDINGS = [("r", "refresh_repos", "Refresh global repo state")]

    def compose(self):
        with Container():
            yield LazyGithubHeader()
            yield MainViewPane()
            yield LazyGithubFooter()

    def action_refresh_repos(self):
        self.update_state()

    @work(thread=True)
    async def update_state(self):
        log("Refreshing global repo state")
        user = g.github_client().get_user()
        repos = user.get_repos()
        repo_list = self.query_one(ReposOptionsList)
        repo_list.clear_options()
        repo_list.add_options([Option(f"{r.name}", id=r.id) for r in repos])

    async def on_mount(self):
        self.update_state()
