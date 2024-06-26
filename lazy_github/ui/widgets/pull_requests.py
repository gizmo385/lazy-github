from typing import Dict

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.coordinate import Coordinate
from textual.widgets import Label, ListItem, ListView, Markdown, RichLog, Rule, TabPane

from lazy_github.lib.github.client import GithubClient
from lazy_github.lib.github.pull_requests import get_diff, get_reviews
from lazy_github.lib.messages import IssuesAndPullRequestsFetched, PullRequestSelected
from lazy_github.lib.string_utils import bold, link, pluralize
from lazy_github.models.github import FullPullRequest, PartialPullRequest, Review, ReviewState
from lazy_github.ui.widgets.command_log import log_event
from lazy_github.ui.widgets.common import LazyGithubContainer, LazyGithubDataTable


class PullRequestsContainer(LazyGithubContainer):
    """
    This container includes the primary datatable for viewing pull requests on the UI.
    """

    def __init__(self, client: GithubClient, *args, **kwargs) -> None:
        self.client = client
        self.pull_requests: Dict[int, PartialPullRequest] = {}
        self.status_column_index = -1
        self.number_column_index = -1
        self.title_column_index = -1
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        self.border_title = "[2] Pull Requests"
        yield LazyGithubDataTable(id="pull_requests_table")

    @property
    def table(self) -> LazyGithubDataTable:
        return self.query_one("#pull_requests_table", LazyGithubDataTable)

    def on_mount(self) -> None:
        self.table.cursor_type = "row"
        self.table.add_column("Status", key="status")
        self.table.add_column("Number", key="number")
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
            rows.append((pr.state, pr.number, pr.user.login, pr.title))
        self.table.add_rows(rows)

    async def get_selected_pr(self) -> PartialPullRequest:
        pr_number_coord = Coordinate(self.table.cursor_row, self.number_column_index)
        number = self.table.get_cell_at(pr_number_coord)
        # full_pr = pr_api.get_pull_request(self.client, number)
        return self.pull_requests[number]

    @on(LazyGithubDataTable.RowSelected, "#pull_requests_table")
    async def pr_selected(self):
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
                date = self.pr.merged_at.strftime("%x at %X")
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
        diff = await get_diff(self.client, self.pr)
        self.query_one("#diff_contents", RichLog).write(diff)

    def on_mount(self) -> None:
        self.fetch_diff()


class PrReview(Container):
    def __init__(self, review: Review) -> None:
        super().__init__()
        self.review = review

    def compose(self) -> ComposeResult:
        # TODO: Color the review text baesd on the state
        if self.review.state == ReviewState.APPROVED:
            pass
        yield Label(f"Review from {self.review.user.login} ({self.review.state.title()}")
        yield Markdown(self.review.body)
        for comment in self.review.comments:
            if comment.user:
                created_at = comment.created_at.strftime("%x at %X")
                yield Label(f"Comment from {comment.user.login} at {created_at}")
                yield Markdown(comment.body)


class PrConversationTabPane(TabPane):
    def __init__(self, client: GithubClient, pr: FullPullRequest) -> None:
        super().__init__("Conversation", id="conversation_pane")
        self.client = client
        self.pr = pr

    def compose(self) -> ComposeResult:
        yield ListView(id="conversation_elements")

    @property
    def conversation_elements(self) -> ListView:
        return self.query_one("#conversation_elements", ListView)

    @work
    async def fetch_conversation(self):
        # TODO: Okay, so the review API in Github is weird. There are 3 APIs we might need to leverage here.
        #
        # 1. The conversation API, which contains comments that happen separately from a review. Unclear if these
        # actually show up for PRs or if they're only actually present on issues (need to find an example).
        # 2. The reviews API, which returns distinct reviews and the comments that accompany them. This will be
        # necessary to setup a list of distinct threads of a review conversation that are happening.
        # 3. The review comments API, which pulls comments for a particular review. It doesn't look like the reviews API
        # actually has the full conversation associated with a review, so might need to query this as well :(
        reviews = await get_reviews(self.client, self.pr)
        for review in reviews:
            log_event(f"Adding  review to the view with {len(review.comments)} comments")
            self.conversation_elements.append(ListItem(PrReview(review)))
        # comments = self.pr.get_issue_comments()
        # reviews = self.pr.get_reviews()
        # review_comments = self.pr.get_review_comments()
        # self.render_conversation(comments, reviews, review_comments)

    def on_mount(self) -> None:
        self.fetch_conversation()
