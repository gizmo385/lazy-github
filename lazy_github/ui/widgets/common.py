from typing import Iterable

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.events import Blur
from textual.widgets import DataTable, Input
from textual.widgets.data_table import CellType


class LazyGithubDataTable(DataTable):
    "An data table for LazyGithub that provides some more vim-like bindings"

    BINDINGS = [
        # Add space as an additional selection key
        ("space", "select"),
        # Add some vim bindings
        ("j", "cursor_down"),
        ("k", "cursor_up"),
        ("l", "scroll_right"),
        ("h", "scroll_left"),
        ("g", "scroll_top"),
        ("G", "scroll_bottom"),
        ("^", "page_left"),
        ("$", "page_right"),
    ]


class LazyGithubDataTableSearchInput(Input):
    def _on_blur(self, event: Blur) -> None:
        if not self.value.strip():
            # If we lose focus and the content is empty, hide it
            self.can_focus = False
            self.display = False
        return super()._on_blur(event)


class SearchableLazyGithubDataTable(Vertical):
    BINDINGS = [("/", "focus_search", "Search")]

    DEFAULT_CSS = """
    LazyGithubDataTableSearchInput {
        margin-bottom: 1;
    }
    """

    def __init__(
        self, table_id: str, search_input_id: str, sort_key: str, *args, reverse_sort: bool = False, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.table = LazyGithubDataTable(id=table_id)
        self.search_input = LazyGithubDataTableSearchInput(placeholder="Search...", id=search_input_id)
        self.search_input.display = False
        self.search_input.can_focus = False
        self.sort_key = sort_key
        self.reverse_sort = reverse_sort
        self._rows_cache = []

    def sort(self):
        self.table.sort(self.sort_key, reverse=self.reverse_sort)

    def compose(self) -> ComposeResult:
        yield self.search_input
        yield self.table

    async def action_focus_search(self) -> None:
        self.search_input.can_focus = True
        self.search_input.display = True
        self.search_input.focus()

    def clear_rows(self):
        self.table.clear()

    def add_rows(self, rows: Iterable[Iterable[CellType]]) -> None:
        self._set_rows(rows)
        self._rows_cache = rows

    def _set_rows(self, rows: Iterable[Iterable[CellType]]) -> None:
        self.table.clear()
        self.table.add_rows(rows)
        self.sort()

    @on(Input.Submitted)
    async def handle_submitted_search(self) -> None:
        search_query = self.search_input.value.strip().lower()
        filtered_rows: Iterable[Iterable] = []
        for row in self._rows_cache:
            if search_query in str(row).lower() or not search_query:
                filtered_rows.append(row)

        self._set_rows(filtered_rows)
        self.table.focus()


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
