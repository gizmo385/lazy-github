from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Placeholder, Static, OptionList
from textual.widgets.option_list import Option


class LazyGithubPlaceholder(Placeholder):
    DEFAULT_CSS = """
    LazyGithubPlaceholder {
        height: 10fr;
        border: ascii white;
    }
    """


class LazyGithubMenu(Container):
    DEFAULT_CSS = """
    LazyGithubMenu {
        height: 10fr;
        border: ascii white;
        display: block;
    }
    """


class ReposOptionsList(OptionList):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.add_options(
            [
                Option("Loading...", id="loading-repos"),
            ]
        )
        self.run_worker(self.update_repos, exclusive=True)

    async def update_repos(self) -> None:
        self.clear_options()
        self.add_options(
            [
                Option("Loading...", id="loading-repos"),
            ]
        )
        # repos = self.github.get_repos()
        # self.clear_options()
        # for repo in repos:
        # repo_ref = f"{repo.owner}/{repo.name}"
        # self.add_option(Option(repo_ref, id=repo_ref))


class ReposContainer(LazyGithubMenu):
    def compose(self) -> ComposeResult:
        self.border_title = "[1] Repositories"
        yield ReposOptionsList()


class PullRequestsContainer(LazyGithubMenu):
    def compose(self) -> ComposeResult:
        self.border_title = "[2] Pull Requests"
        yield Static("hello")


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

    def compose(self) -> ComposeResult:
        yield ReposContainer(id="Repos")
        yield PullRequestsContainer(id="PRs")
        yield IssuesContainer(id="Issues")
        yield ActionsContainer(id="Actions")


class MainViewPane(Container):
    def compose(self) -> ComposeResult:
        yield Menus()
        yield ScratchSpaceContainer(id="Scratch")


class LazyGithubHeader(Header):
    pass


class LazyGithubFooter(Footer):
    pass


class LazyGithub(App):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container():
            yield LazyGithubHeader()
            yield MainViewPane()
            yield LazyGithubFooter()

    def on_key(self, event: events.Key) -> None:
        pass


if __name__ == "__main__":
    app = LazyGithub()
    app.run()

# Sketching how the UI should look
_sketch = """
-------------------------------------------------------------------------------------------
|                                                                                         |
|   -- [1] Repos ----------      ---- Scratch Working Space for Selected Thing ---------  |
|   | gizmo385/dotfiles   |      |                                                     |  |
|   | linux/linux         |      |                                                     |  |
|   | discord/discord     |      |                                                     |  |
|   |                     |      |                                                     |  |
|   |                     |      |                                                     |  |
|   |                     |      |                                                     |  |
|   |                     |      |                                                     |  |
|   ------------[1 / 3]----      |                                                     |  |
|                                |                                                     |  |
|   -- [2] Pull Requests --      |                                                     |  |
|   | #12345: Do thing    |      |                                                     |  |
|   | #54321: Break thing |      |                                                     |  |
|   | #67890: Fix thing   |      |                                                     |  |
|   | #24680: Wait what   |      |                                                     |  |
|   |                     |      |                                                     |  |
|   |                     |      |                                                     |  |
|   |                     |      |                                                     |  |
|   ------------[3 / 4]----      |                                                     |  |
|                                |                                                     |  |
|   -- [3] Issues ---------      |                                                     |  |
|   | #57405: It's broke  |      |                                                     |  |
|   | #80280: It's slow   |      |                                                     |  |
|   | #12900: Add feature |      |                                                     |  |
|   | #24680: Support nix |      |                                                     |  |
|   |                     |      |                                                     |  |
|   |                     |      |                                                     |  |
|   |                     |      |                                                     |  |
|   ------------[1 / 4]----      |                                                     |  |
|                                |                                                     |  |
|   -- [4] Actions Log ----      |                                                     |  |
|   | #4: Build Running   |      |                                                     |  |
|   | #3: Build Success   |      |                                                     |  |
|   | #2: Build Canceled  |      |                                                     |  |
|   | #1: Build Faileds   |      |                                                     |  |
|   |                     |      |                                                     |  |
|   |                     |      |                                                     |  |
|   |                     |      |                                                     |  |
|   ------------[1 / 4]----      -------------------------------------------------------  |
|                                                                                         |
-------------------------------------------------------------------------------------------
"""
