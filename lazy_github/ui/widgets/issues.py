from typing import Dict

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, VerticalScroll
from textual.coordinate import Coordinate
from textual.widgets import Label, Markdown, Rule, TabPane

from lazy_github.lib.github.client import GithubClient
from lazy_github.lib.github.issues import get_comments
from lazy_github.lib.messages import IssuesAndPullRequestsFetched, IssueSelected
from lazy_github.lib.string_utils import link
from lazy_github.models.github import Issue, IssueState
from lazy_github.ui.widgets.command_log import log_event
from lazy_github.ui.widgets.common import LazyGithubContainer, LazyGithubDataTable, SearchableLazyGithubDataTable
from lazy_github.ui.widgets.conversations import IssueCommentContainer


class IssuesContainer(LazyGithubContainer):
    issues: Dict[int, Issue] = {}
    status_column_index = -1
    number_column_index = -1
    title_column_index = -1

    def compose(self) -> ComposeResult:
        self.border_title = "[3] Issues"
        yield SearchableLazyGithubDataTable(
            id="searchable_issues_table",
            table_id="issues_table",
            search_input_id="issues_search",
            sort_key="number",
            reverse_sort=True,
        )

    @property
    def searchable_table(self) -> SearchableLazyGithubDataTable:
        return self.query_one("#searchable_issues_table", SearchableLazyGithubDataTable)

    @property
    def table(self) -> LazyGithubDataTable:
        return self.query_one("#issues_table", LazyGithubDataTable)

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
        self.searchable_table.add_rows(rows)

    async def get_selected_issue(self) -> Issue:
        pr_number_coord = Coordinate(self.table.cursor_row, self.number_column_index)
        number = self.table.get_cell_at(pr_number_coord)
        return self.issues[number]

    @on(LazyGithubDataTable.RowSelected, "#issues_table")
    async def issue_selected(self) -> None:
        issue = await self.get_selected_issue()
        log_event(f"Selected Issue: #{issue.number}")
        self.post_message(IssueSelected(issue))


class IssueOverviewTabPane(TabPane):
    DEFAULT_CSS = """
    IssueOverviewTabPane {
        overflow-y: auto;
    }
    """

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


class IssueConversationTabPane(TabPane):
    def __init__(self, client: GithubClient, issue: Issue) -> None:
        super().__init__("Comments", id="issue_conversation")
        self.client = client
        self.issue = issue

    @property
    def comments(self) -> VerticalScroll:
        return self.query_one("#issue_conversation", VerticalScroll)

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="issue_conversation")

    def on_mount(self) -> None:
        self.loading = False
        self.fetch_issue_comments()

    @work
    async def fetch_issue_comments(self) -> None:
        comments = await get_comments(self.client, self.issue)
        self.comments.remove_children()
        if comments:
            for comment in comments:
                comment_container = IssueCommentContainer(self.client, self.issue, comment)
                self.comments.mount(comment_container)
        else:
            self.comments.mount(Label("No comments available"))
        self.loading = True
