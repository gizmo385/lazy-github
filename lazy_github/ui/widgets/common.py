from asyncio import Lock
from typing import Awaitable, Callable

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.events import Blur
from textual.widgets import DataTable, Footer, Input
from textual.widgets.data_table import RowDoesNotExist

from lazy_github.lib.bindings import LazyGithubBindings

TABLE_POPULATION_FUNCTION = Callable[[int, int], Awaitable[dict[str, tuple[str | int, ...]]]]


class LazyGithubFooter(Footer):
    def __init__(self) -> None:
        super().__init__(show_command_palette=False)


class _VimLikeDataTable(DataTable[str | int]):
    "An data table for LazyGithub that provides some more vim-like bindings"

    BINDINGS = [
        LazyGithubBindings.SELECT_ENTRY,
        LazyGithubBindings.TABLE_DOWN,
        LazyGithubBindings.TABLE_PAGE_DOWN,
        LazyGithubBindings.TABLE_CURSOR_UP,
        LazyGithubBindings.TABLE_PAGE_UP,
        LazyGithubBindings.TABLE_SCROLL_RIGHT,
        LazyGithubBindings.TABLE_PAGE_RIGHT,
        LazyGithubBindings.TABLE_SCROLL_LEFT,
        LazyGithubBindings.TABLE_PAGE_LEFT,
        LazyGithubBindings.TABLE_SCROLL_TOP,
        LazyGithubBindings.TABLE_SCROLL_BOTTOM,
        LazyGithubBindings.TABLE_PAGE_LEFT,
        LazyGithubBindings.TABLE_PAGE_RIGHT,
    ]


class ToggleableSearchInput(Input):
    def _on_blur(self, event: Blur) -> None:
        if not self.value.strip():
            # If we lose focus and the content is empty, hide it
            self.can_focus = False
            self.display = False
        return super()._on_blur(event)


class SearchableDataTable(Vertical):
    BINDINGS = [LazyGithubBindings.SEARCH_TABLE]

    DEFAULT_CSS = """
    ToggleableSearchInput {
        margin-bottom: 1;
    }
    """

    def __init__(
        self, table_id: str, search_input_id: str, sort_key: str, *args, reverse_sort: bool = False, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.table = _VimLikeDataTable(id=table_id)
        self.search_input = ToggleableSearchInput(placeholder="Search...", id=search_input_id)
        self.search_input.display = False
        self.search_input.can_focus = False
        self.sort_key = sort_key
        self.reverse_sort = reverse_sort
        self._rows_cache: dict[str, tuple[str | int, ...]] = {}

    def sort_table(self):
        self.table.sort(self.sort_key, reverse=self.reverse_sort)

    def compose(self) -> ComposeResult:
        yield self.search_input
        yield self.table

    async def action_focus_search(self) -> None:
        """Focus on the search"""
        self.search_input.can_focus = True
        self.search_input.display = True
        self.search_input.focus()

    def clear_rows(self):
        """Removes all rows currently displayed and tracked in this table"""
        self._rows_cache = {}
        self.table.clear()

    def add_row(self, cells: tuple[str | int, ...], key: str) -> None:
        """Add an individual row with the specified key to the table. The table will be sorted after the key is added"""
        try:
            # Before we add the row, we want to see if the key already exists
            if key in self._rows_cache:
                self.table.remove_row(key)
        except RowDoesNotExist:
            # If the row doesn't exist, then something already removed it and we can move on
            pass

        self._rows_cache[key] = cells
        self.table.add_row(*cells, key=key)

        self.table.sort(self.sort_key, reverse=self.reverse_sort)

    def add_rows(self, rows: dict[str, tuple[str | int, ...]]) -> None:
        """Add new rows to the currently displayed table and cache"""
        self._rows_cache.update(rows)
        for key, row in rows.items():
            self.table.add_row(*row, key=key)

    @on(Input.Submitted)
    async def handle_submitted_search(self) -> None:
        """When a search is submitted, triggers the filter for the entries in the table"""
        search_query = self.search_input.value.strip().lower()
        filtered_rows: dict[str, tuple[str | int, ...]] = {}
        for key, row in self._rows_cache.items():
            if search_query in str(row).lower() or not search_query:
                filtered_rows[key] = row

        self.table.clear()
        self.add_rows(filtered_rows)
        self.table.focus()


class LazilyLoadedDataTable(SearchableDataTable):
    """A searchable data table that is lazily loaded when you have viewed the currently loaded data"""

    def __init__(
        self,
        table_id: str,
        search_input_id: str,
        sort_key: str,
        load_function: TABLE_POPULATION_FUNCTION | None,
        batch_size: int,
        *args,
        load_more_data_buffer: int = 5,
        reverse_sort: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(table_id, search_input_id, sort_key, *args, reverse_sort=reverse_sort, **kwargs)
        self.fetch_lock = Lock()
        self.load_function = load_function
        self.batch_size = batch_size
        self.load_more_data_buffer = load_more_data_buffer
        self.current_batch = 0

        # We initialize this to true and set it to false later if we believe we've run out of data to load from the load
        # function.
        self.can_load_more = True

    def change_load_function(self, new_load_function: TABLE_POPULATION_FUNCTION | None) -> None:
        self.load_function = new_load_function

    def clear_rows(self):
        """Removes all rows currently displayed and tracked in this table"""
        super().clear_rows()
        self.current_batch = 0
        self.can_load_more = True

    @work
    async def load_more_data(self, row_highlighted: DataTable.RowHighlighted) -> None:
        async with self.fetch_lock:
            rows_remaining = len(self._rows_cache) - row_highlighted.cursor_row
            if not (self.can_load_more and self.load_function):
                return

            if rows_remaining > self.load_more_data_buffer:
                return

            additional_data = await self.load_function(self.batch_size, self.current_batch + 1)
            self.current_batch += 1
            if len(additional_data) == 0:
                self.can_load_more = False

            self.add_rows(additional_data)

    @on(DataTable.RowHighlighted)
    async def check_highlighted_row_boundary(self, row_highlighted: DataTable.RowHighlighted) -> None:
        self.load_more_data(row_highlighted)


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
        min-height: 40%;
        border: solid $success;
    }
    """
