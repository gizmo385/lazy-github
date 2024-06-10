import lazy_github.lib.github as g

from textual import log, work, on
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Footer,
    Static,
    OptionList,
)
from textual.widgets.option_list import Option


class LazyGithubMenu(Container):
    DEFAULT_CSS = """
    LazyGithubMenu {
        display: block;
        border: ascii white;
        height: 20%;
    }

    LazyGithubMenu:focus-within {
        height: 40%;
    }
    """


class ReposOptionsList(OptionList):
    pass


class ReposContainer(LazyGithubMenu):
    def compose(self) -> ComposeResult:
        self.border_title = "[1] Repositories"
        yield ReposOptionsList()

    @work(thread=True)
    def select_repo(self, repo_id):
        repo = g.github_client().get_repo(repo_id)
        self.app.query_one(CurrentlySelectedRepo).current_repo = repo.full_name

    @on(ReposOptionsList.OptionSelected)
    def repo_selected(self, option: Option):
        log(f"Selected repo {option.option_id}")
        self.select_repo(option.option_id)


class PullRequestsOptionsList(OptionList):
    pass


class PullRequestsContainer(LazyGithubMenu):
    def compose(self) -> ComposeResult:
        self.border_title = "[2] Pull Requests"
        yield PullRequestsOptionsList()


class IssuesContainer(LazyGithubMenu):
    def compose(self) -> ComposeResult:
        self.border_title = "[3] Issues"
        yield Static("hello")


class ActionsContainer(LazyGithubMenu):
    def compose(self) -> ComposeResult:
        self.border_title = "[4] Actions"
        yield Static("hello")


class ScratchSpaceContainer(Container):
    DEFAULT_CSS = """
    ScratchSpaceContainer {
        height: 100%;
        width: 60%;
        border: ascii white;
        dock: right;
    }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "Scratch space"
        yield Static("Hello")


class Menus(Container):
    DEFAULT_CSS = """
    Menus {
        height: 100%;
        width: 40%;
        dock: left;
    }
    """

    BINDINGS = [
        ("1", "focus_repos"),
        ("2", "focus_pulls"),
        ("3", "focus_issues"),
        ("4", "focus_actions"),
    ]

    def action_focus_repos(self):
        # TODO: This doesn't appear to be working
        self.query_one(ReposContainer).focus()

    def action_focus_pulls(self):
        self.query_one(PullRequestsContainer).focus()

    def action_focus_issues(self):
        self.query_one(IssuesContainer).focus()

    def action_focus_actions(self):
        self.query_one(ActionsContainer).focus()

    def compose(self) -> ComposeResult:
        yield ReposContainer(id="repos", classes="focused")
        yield PullRequestsContainer(id="pull_requests", classes="unfocused")
        yield IssuesContainer(id="issues", classes="unfocused")
        yield ActionsContainer(id="actions", classes="unfocused")


class MainViewPane(Container):
    def compose(self) -> ComposeResult:
        yield Menus()
        yield ScratchSpaceContainer(id="Scratch")


class CurrentlySelectedRepo(Widget):
    current_repo = reactive("None")

    def render(self):
        return f"Current repo: {self.current_repo}"


class LazyGithubHeader(Container):
    DEFAULT_CSS = """
    LazyGithubHeader {
        height: 10%;
        width: 100%;
        border: ascii white;
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
