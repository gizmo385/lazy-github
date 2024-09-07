from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Markdown, TabPane

LAZY_GITHUB_INFO = """
# LazyGithub: A Terminal UI For GitHub

LazyGithub is a terminal UI for interacting with GitHub. You can get started by selecting one of the repositories listed
in the table on the left. Once you have selected a repository, any issues, pull requests, and action workflows will be
retrieved and displayed below it.

**Issues, pull requests, and action lists can also be interacted with!**

## Pull Requests

TODO

## Issues

TODO

## Actions

WIP
""".strip()


class LazyGithubInfoTabPane(TabPane):
    DEFAULT_CSS = """
    .subtitle {
        align: center top;
    }
    """

    def __init__(self) -> None:
        super().__init__("Introduction")

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Markdown(LAZY_GITHUB_INFO)
