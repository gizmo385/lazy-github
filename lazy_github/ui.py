from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Placeholder


# TODO:
# 1: Work out how to title the little mini containers
# 2: Wrap the menus in a scrollpanel incase they get too big
# 3: Start pulling in Github information (how do we auth?)
# 3.a: Let's do pull requests first since they're straightforward


class LazyGithubMenu(Placeholder):
    DEFAULT_CSS = """
    LazyGithubMenu {
        height: 10fr;
        border: solid red;
    }
    """


class ReposContainer(LazyGithubMenu):
    pass


class PullRequestsContainer(LazyGithubMenu):
    pass


class IssuesContainer(LazyGithubMenu):
    pass


class ActionsContainer(LazyGithubMenu):
    pass


class ScratchSpaceContainer(Placeholder):
    DEFAULT_CSS = """
    ScratchSpaceContainer {
        margin: 1
    }
    """
    pass


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
    LazyGithub().run()

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
