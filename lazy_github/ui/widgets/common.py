from textual.containers import Container
from textual.widgets import DataTable


class LazyGithubDataTable(DataTable):
    "An data table for LazyGithub that provides some more vim-like bindings"

    BINDINGS = [("j", "cursor_down"), ("k", "cursor_up"), ("space", "select")]


class LazyGithubContainer(Container):
    """
    Base container class for focusible containers within the Lazy Github UI
    """

    DEFAULT_CSS = """
    LazyGithubContainer {
        display: block;
        border: solid $primary-lighten-3;
    }

    LazyGithubContainer:focus-within {
        height: 40%;
        border: solid $success;
    }
    """
