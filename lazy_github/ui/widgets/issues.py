from typing import Dict

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, VerticalScroll
from textual.coordinate import Coordinate
from textual.widgets import DataTable, Label, Markdown, Rule, TabPane
from textual.widgets.data_table import CellDoesNotExist

from lazy_github.lib.bindings import LazyGithubBindings
from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.github.issues import get_comments, list_issues
from lazy_github.lib.logging import lg
from lazy_github.lib.messages import IssuesAndPullRequestsFetched, IssueSelected, NewCommentCreated
from lazy_github.lib.utils import link
from lazy_github.models.github import Issue, IssueState, PartialPullRequest
from lazy_github.ui.screens.edit_issue import EditIssueModal
from lazy_github.ui.screens.new_comment import NewCommentModal
from lazy_github.ui.widgets.common import LazilyLoadedDataTable, LazyGithubContainer
from lazy_github.ui.widgets.conversations import IssueCommentContainer


def issue_to_cell(issue: Issue) -> tuple[str | int, ...]:
    return (issue.number, str(issue.state), issue.user.login, issue.title)


class IssuesContainer(LazyGithubContainer):
    BINDINGS = [LazyGithubBindings.EDIT_ISSUE]

    issues: Dict[int, Issue] = {}
    status_column_index = -1
    number_column_index = -1
    title_column_index = -1

    def compose(self) -> ComposeResult:
        self.border_title = "[3] Issues"
        yield LazilyLoadedDataTable(
            id="searchable_issues_table",
            table_id="issues_table",
            search_input_id="issues_search",
            sort_key="number",
            load_function=None,
            batch_size=30,
            reverse_sort=True,
        )

    async def fetch_more_issues(self, batch_size: int, batch_to_fetch: int) -> list[tuple[str | int, ...]]:
        if not LazyGithubContext.current_repo:
            return []

        next_page = await list_issues(
            LazyGithubContext.current_repo,
            LazyGithubContext.config.issues.state_filter,
            LazyGithubContext.config.issues.owner_filter,
            page=batch_to_fetch,
            per_page=batch_size,
        )

        new_issues = [i for i in next_page if not isinstance(i, PartialPullRequest)]
        self.issues.update({i.number: i for i in new_issues})

        return [issue_to_cell(i) for i in new_issues]

    @property
    def searchable_table(self) -> LazilyLoadedDataTable:
        return self.query_one("#searchable_issues_table", LazilyLoadedDataTable)

    @property
    def table(self) -> DataTable:
        return self.query_one("#issues_table", DataTable)

    def on_mount(self) -> None:
        self.table.cursor_type = "row"
        self.table.add_column("#", key="number")
        self.table.add_column("Status", key="status")
        self.table.add_column("Author", key="author")
        self.table.add_column("Title", key="title")

        self.status_column_index = self.table.get_column_index("status")
        self.number_column_index = self.table.get_column_index("number")
        self.title_column_index = self.table.get_column_index("title")

    async def on_issues_and_pull_requests_fetched(self, message: IssuesAndPullRequestsFetched) -> None:
        message.stop()
        self.table.clear()
        self.issues = {}

        rows = []
        for issue in message.issues:
            self.issues[issue.number] = issue
            rows.append((issue.number, issue.state, issue.user.login, issue.title))
        self.searchable_table.set_rows(rows)
        self.searchable_table.change_load_function(self.fetch_more_issues)
        self.searchable_table.can_load_more = True
        self.searchable_table.current_batch = 1

    async def get_selected_issue(self) -> Issue:
        pr_number_coord = Coordinate(self.table.cursor_row, self.number_column_index)
        number = self.table.get_cell_at(pr_number_coord)
        return self.issues[number]

    async def action_edit_issue(self) -> None:
        try:
            issue = await self.get_selected_issue()
            self.app.push_screen(EditIssueModal(issue))
        except CellDoesNotExist:
            self.notify("No issue currently selected", severity="error")

    @on(DataTable.RowSelected, "#issues_table")
    async def issue_selected(self) -> None:
        issue = await self.get_selected_issue()
        lg.info(f"Selected Issue: #{issue.number}")
        self.post_message(IssueSelected(issue))


class IssueOverviewTabPane(TabPane):
    DEFAULT_CSS = """
    IssueOverviewTabPane {
        overflow-y: auto;
    }
    """

    BINDINGS = [LazyGithubBindings.EDIT_ISSUE]

    def __init__(self, issue: Issue) -> None:
        super().__init__("Overview", id="issue_overview_pane")
        self.issue = issue

    def compose(self) -> ComposeResult:
        issue_link = link(f"(#{self.issue.number})", self.issue.html_url)
        user_link = link(self.issue.user.login, self.issue.user.html_url)

        if self.issue.state == IssueState.OPEN:
            issue_status = "[frame green]Open[/frame green]"
        else:
            issue_status = "[frame purple]Closed[/frame purple]"

        with ScrollableContainer():
            yield Label(f"{issue_status} [b]{self.issue.title}[b] {issue_link} by {user_link}")

            yield Rule()
            yield Markdown(self.issue.body)

    def action_edit_issue(self) -> None:
        self.app.push_screen(EditIssueModal(self.issue))


class IssueConversationTabPane(TabPane):
    BINDINGS = [LazyGithubBindings.NEW_COMMENT]

    def __init__(self, issue: Issue) -> None:
        super().__init__("Comments", id="issue_conversation")
        self.issue = issue

    @property
    def comments(self) -> VerticalScroll:
        return self.query_one("#issue_conversation", VerticalScroll)

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="issue_conversation")

    @work
    async def new_comment_flow(self) -> None:
        new_comment = await self.app.push_screen_wait(NewCommentModal(self.issue.repo, self.issue, None))
        if new_comment is not None:
            self.comments.mount(IssueCommentContainer(self.issue, new_comment))

    @on(NewCommentCreated)
    def handle_new_comment_added(self, message: NewCommentCreated) -> None:
        self.comments.mount(IssueCommentContainer(self.issue, message.comment))

    async def action_new_comment(self) -> None:
        self.new_comment_flow()

    def on_mount(self) -> None:
        self.loading = True
        self.fetch_issue_comments()

    @work
    async def fetch_issue_comments(self) -> None:
        comments = await get_comments(self.issue)
        self.comments.remove_children()
        if comments:
            for comment in comments:
                comment_container = IssueCommentContainer(self.issue, comment)
                self.comments.mount(comment_container)
        else:
            self.comments.mount(Label("No comments available"))
        self.loading = False
