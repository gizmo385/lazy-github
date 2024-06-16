from github.PullRequest import PullRequest
from textual import log, on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Footer,
    Label,
    RichLog,
    TabbedContent,
    TabPane,
)

import lazy_github.lib.github as g
from lazy_github.lib.constants import IS_FAVORITED
from lazy_github.ui.widgets.command_log import CommandLogSection, log_event
from lazy_github.ui.widgets.common import LazyGithubContainer, LazyGithubDataTable
from lazy_github.ui.widgets.repositories import ReposContainer, RepoSelected

# Color palletes
# https://coolors.co/84ffc9-aab2ff-eca0ff


class CurrentlySelectedRepo(Widget):
    current_repo_name: reactive[str | None] = reactive(None)

    def render(self):
        if self.current_repo_name:
            return f"Current repo: [green]{self.current_repo_name}[/green]"
        else:
            return "No repository selected"


class LazyGithubStatusSummary(Container):
    DEFAULT_CSS = """
    LazyGithubStatusSummary {
        height: 10%;
        width: 100%;
        border: solid $secondary;
    }
    """

    def compose(self):
        yield CurrentlySelectedRepo()


class LazyGithubFooter(Footer):
    pass


class PullRequestsContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[2] Pull Requests"
        yield LazyGithubDataTable(id="pull_requests_table")

    @property
    def table(self) -> LazyGithubDataTable:
        return self.query_one("#pull_requests_table", LazyGithubDataTable)

    def on_mount(self):
        self.table.cursor_type = "row"
        self.table.add_column(IS_FAVORITED, key="favorite")
        self.table.add_column("Status", key="status")
        self.table.add_column("Number", key="number")
        self.table.add_column("Title", key="title")

    async def on_repo_selected(self, message: RepoSelected) -> None:
        # TODO: Load the PRs for the selected repo
        message.stop()

    @work()
    async def select_pull_request(self, pr: PullRequest) -> str:
        log_event(f"Selected PR {pr}")
        scratch_space = self.app.query_one(ScratchSpaceContainer)
        scratch_space.show_pr_details(pr)

    @work
    async def get_selected_pr(self) -> PullRequest:
        pass

    @on(LazyGithubDataTable.RowSelected, "#repos_table")
    async def pr_selected(self):
        # Bubble a message up indicating that a repo was selected
        pr = await self.get_selected_pr()
        log_event(f"Selected PR {pr.title}")


class IssuesContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[3] Issues"
        yield LazyGithubDataTable(id="pull_requests_table")

    async def on_repo_selected(self, message: RepoSelected) -> None:
        # TODO: Load the issues for the selected repo
        message.stop()


class ActionsContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[4] Actions"
        yield LazyGithubDataTable(id="actions_table")

    async def on_repo_selected(self, message: RepoSelected) -> None:
        # TODO: Load the actions for the selected repo
        message.stop()


class PrOverviewTabPane(TabPane):
    def __init__(self, pr: PullRequest) -> None:
        super().__init__("Overview", id="overview")
        self.pr = pr

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                yield Label(f"[b]{self.pr.title}[/b]", id="pr_title")
                yield Label(f"{self.pr.head.ref} --{self.pr.commits}--> {self.pr.base.ref}")
            yield Label(f"[b]Description[/b]: {self.pr.body}", id="pr_description")


class PrDiffTabPane(TabPane):
    def __init__(self, pr: PullRequest) -> None:
        super().__init__("Diff", id="diff_pane")
        self.pr = pr

    def compose(self) -> ComposeResult:
        yield RichLog(id="diff_contents", highlight=True)

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
        self.border_title = "[5] Details"
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

    @property
    def pull_requests(self) -> PullRequestsContainer:
        return self.query_one("#pull_requests", PullRequestsContainer)

    @property
    def issues(self) -> IssuesContainer:
        return self.query_one("#issues", IssuesContainer)

    @property
    def actions(self) -> ActionsContainer:
        return self.query_one("#actions", ActionsContainer)

    async def on_repo_selected(self, message: RepoSelected) -> None:
        self.pull_requests.post_message(message)
        self.issues.post_message(message)
        self.actions.post_message(message)


class DetailsPane(Container):
    def compose(self) -> ComposeResult:
        yield ScratchSpaceContainer(id="Scratch")
        yield CommandLogSection()


class MainViewPane(Container):
    BINDINGS = [
        # ("1", "focus_section('ReposOptionsList')"),
        # ("2", "focus_section('PullRequestsOptionsList')"),
        # ("3", "focus_section('IssuesOptionList')"),
        # ("4", "focus_section('ActionsOptionList')"),
        # ("5", "focus_section('#scratch_space_tabs')"),
        # ("6", "focus_section('LazyGithubCommandLog')"),
    ]

    def action_focus_section(self, selector: str) -> None:
        self.query_one(selector).focus()

    def compose(self) -> ComposeResult:
        yield SelectionsPane()
        yield DetailsPane()


class LazyGithubMainScreen(Screen):
    BINDINGS = [("r", "refresh_repos", "Refresh global repo state")]

    def compose(self):
        with Container():
            yield LazyGithubStatusSummary()
            yield MainViewPane()
            yield LazyGithubFooter()
