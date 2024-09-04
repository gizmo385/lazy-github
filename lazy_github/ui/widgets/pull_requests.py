from httpx import HTTPStatusError
from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, VerticalScroll
from textual.coordinate import Coordinate
from textual.widgets import Label, Markdown, RichLog, Rule, TabPane

from lazy_github.lib.github.client import GithubClient
from lazy_github.lib.github.issues import get_comments
from lazy_github.lib.github.pull_requests import (
    get_diff,
    get_reviews,
    reconstruct_review_conversation_hierarchy,
)
from lazy_github.lib.messages import IssuesAndPullRequestsFetched, PullRequestSelected
from lazy_github.lib.string_utils import bold, link, pluralize
from lazy_github.models.github import FullPullRequest, PartialPullRequest
from lazy_github.ui.screens.new_comment import NewCommentModal
from lazy_github.ui.widgets.command_log import log_event
from lazy_github.ui.widgets.common import LazyGithubContainer, LazyGithubDataTable, SearchableLazyGithubDataTable
from lazy_github.ui.widgets.conversations import IssueCommentContainer, ReviewContainer


class PullRequestsContainer(LazyGithubContainer):
    """
    This container includes the primary datatable for viewing pull requests on the UI.
    """

    def __init__(self, client: GithubClient, *args, **kwargs) -> None:
        self.client = client
        self.pull_requests: dict[int, PartialPullRequest] = {}
        self.status_column_index = -1
        self.number_column_index = -1
        self.title_column_index = -1
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        self.border_title = "[2] Pull Requests"
        yield SearchableLazyGithubDataTable(
            id="searchable_prs",
            table_id="pull_requests_table",
            search_input_id="pr_search_query",
            sort_key="number",
            reverse_sort=True,
        )

    @property
    def searchable_table(self) -> SearchableLazyGithubDataTable:
        return self.query_one("#searchable_prs", SearchableLazyGithubDataTable)

    @property
    def table(self) -> LazyGithubDataTable:
        return self.searchable_table.table

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
        self.pull_requests = {}

        rows = []
        for pr in message.pull_requests:
            self.pull_requests[pr.number] = pr
            rows.append((pr.number, pr.state, pr.user.login, pr.title))
        self.searchable_table.add_rows(rows)

    async def get_selected_pr(self) -> PartialPullRequest:
        pr_number_coord = Coordinate(self.table.cursor_row, self.number_column_index)
        number = self.table.get_cell_at(pr_number_coord)
        return self.pull_requests[number]

    @on(LazyGithubDataTable.RowSelected, "#pull_requests_table")
    async def pr_selected(self) -> None:
        pr = await self.get_selected_pr()
        log_event(f"Selected PR: #{pr.number}")
        self.post_message(PullRequestSelected(pr))


class PrOverviewTabPane(TabPane):
    DEFAULT_CSS = """
    PrOverviewTabPane {
        overflow-y: auto;
    }
    """

    def __init__(self, pr: FullPullRequest) -> None:
        super().__init__("Overview", id="overview_pane")
        self.pr = pr

    def compose(self) -> ComposeResult:
        pr_link = link(f"(#{self.pr.number})", self.pr.html_url)
        user_link = link(self.pr.user.login, self.pr.user.html_url)
        merge_from = None
        if self.pr.head:
            merge_from = bold(f"{self.pr.head.user.login}:{self.pr.head.ref}")
        merge_to = None
        if self.pr.base:
            merge_to = bold(f"{self.pr.base.user.login}:{self.pr.base.ref}")

        change_summary = " • ".join(
            [
                pluralize(self.pr.commits, "commit", "commits"),
                pluralize(self.pr.changed_files, "file changed", "files changed"),
                f"[green]+{self.pr.additions}[/green]",
                f"[red]-{self.pr.deletions}[/red]",
                f"{merge_from} :right_arrow:  {merge_to}",
            ]
        )

        if self.pr.merged_at:
            merge_status = "[frame purple]Merged[/frame purple]"
        elif self.pr.closed_at:
            merge_status = "[frame red]closed[/frame red]"
        else:
            merge_status = "[frame green]Open[/frame green]"

        with ScrollableContainer():
            yield Label(f"{merge_status} [b]{self.pr.title}[b] {pr_link} by {user_link}")
            yield Label(change_summary)

            if self.pr.merged_at:
                date = self.pr.merged_at.strftime("%c")
                yield Label(f"\nMerged on {date}")

            yield Rule()
            yield Markdown(self.pr.body)


class PrDiffTabPane(TabPane):
    def __init__(self, client: GithubClient, pr: FullPullRequest) -> None:
        super().__init__("Diff", id="diff_pane")
        self.client = client
        self.pr = pr

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield RichLog(id="diff_contents", highlight=True)

    @work
    async def fetch_diff(self):
        diff_contents = self.query_one("#diff_contents", RichLog)
        try:
            diff = await get_diff(self.client, self.pr)
        except HTTPStatusError as hse:
            if hse.response.status_code == 404:
                diff_contents.write("No diff contents found")
            else:
                raise
        else:
            diff_contents.write(diff)
        self.loading = False

    def on_mount(self) -> None:
        self.loading = True
        self.fetch_diff()


class PrConversationTabPane(TabPane):
    BINDINGS = [("n", "new_comment", "New comment")]

    def __init__(self, client: GithubClient, pr: FullPullRequest) -> None:
        super().__init__("Conversation", id="conversation_pane")
        self.client = client
        self.pr = pr

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="pr_comments_and_reviews")

    @property
    def comments_and_reviews(self) -> VerticalScroll:
        return self.query_one("#pr_comments_and_reviews", VerticalScroll)

    @work
    async def fetch_conversation(self) -> None:
        reviews = await get_reviews(self.client, self.pr)
        review_hierarchy = reconstruct_review_conversation_hierarchy(reviews)
        comments = await get_comments(self.client, self.pr)
        self.comments_and_reviews.remove_children()

        handled_comment_node_ids: list[int] = []
        for review in reviews:
            if review.body:
                handled_comment_node_ids.extend([c.id for c in review.comments])
                review_container = ReviewContainer(self.client, self.pr, review, review_hierarchy)
                self.comments_and_reviews.mount(review_container)

        for comment in comments:
            if comment.body and comment.id not in handled_comment_node_ids:
                comment_container = IssueCommentContainer(self.client, self.pr, comment)
                self.comments_and_reviews.mount(comment_container)

        if len(self.comments_and_reviews.children) == 0:
            self.comments_and_reviews.mount(Label("No reviews or comments available"))

        self.loading = False

    def on_mount(self) -> None:
        self.loading = True
        self.fetch_conversation()

    def action_new_comment(self) -> None:
        self.app.push_screen(NewCommentModal(self.client, self.pr.repo, self.pr, None))
