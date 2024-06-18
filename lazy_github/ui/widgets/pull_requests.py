from typing import Dict

from github.PullRequest import PullRequest
from textual import log, on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.coordinate import Coordinate
from textual.widgets import Label, Markdown, RichLog, Rule, TabPane

import lazy_github.lib.github as g
from lazy_github.lib.messages import PullRequestSelected, RepoSelected
from lazy_github.lib.string_utils import pluralize
from lazy_github.ui.widgets.command_log import log_event
from lazy_github.ui.widgets.common import LazyGithubContainer, LazyGithubDataTable


class PullRequestsContainer(LazyGithubContainer):
    """
    This container includes the primary datatable for viewing pull requests on the UI.
    """

    pull_requests: Dict[int, PullRequest] = {}
    status_column_index = -1
    number_column_index = -1
    title_column_index = -1

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

    async def on_repo_selected(self, message: RepoSelected) -> None:
        message.stop()
        self.table.clear()
        self.pull_requests = {}
        pull_requests = message.repo.get_pulls(state="all", sort="updated", direction="desc")
        rows = []
        for pr in pull_requests:
            self.pull_requests[pr.number] = pr
            rows.append((pr.state, pr.number, pr.user.login, pr.title))
        self.table.add_rows(rows)

    async def get_selected_pr(self) -> PullRequest:
        pr_number_coord = Coordinate(self.table.cursor_row, self.number_column_index)
        number = self.table.get_cell_at(pr_number_coord)
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

    def __init__(self, pr: PullRequest) -> None:
        super().__init__("Overview", id="overview_pane")
        self.pr = pr

    def compose(self) -> ComposeResult:
        pr_summary = " • ".join(
            [
                pluralize(self.pr.commits, "commit", "commits"),
                pluralize(self.pr.changed_files, "file changed", "files changed"),
                f"[green]+{self.pr.additions}[/green]",
                f"[red]-{self.pr.deletions}[/red]",
            ]
        )
        with ScrollableContainer():
            yield Label(f"[bold]{self.pr.title}[/bold] [gray](#{self.pr.number})[/gray]")
            yield Label(pr_summary)
            yield Rule()
            yield Markdown(self.pr.body)


class PrDiffTabPane(TabPane):
    BINDINGS = [("j", "scroll_down"), ("k", "scroll_up")]

    def __init__(self, pr: PullRequest) -> None:
        super().__init__("Diff", id="diff_pane")
        self.pr = pr

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield RichLog(id="diff_contents", highlight=True)

    def action_scroll_up(self):
        self.query_one("#diff_contents", RichLog).scroll_up()

    def action_scroll_down(self):
        self.query_one("#diff_contents", RichLog).scroll_down()

    @work
    async def write_diff(self, diff: str) -> None:
        self.query_one("#diff_contents", RichLog).write(diff)

    @work(thread=True)
    def fetch_diff(self):
        diff = g.get_diff(self.pr)
        self.write_diff(diff)

    def on_mount(self) -> None:
        self.fetch_diff()


class PrConversationTabPane(TabPane):
    def __init__(self, pr: PullRequest) -> None:
        super().__init__("Conversation", id="conversation_pane")
        self.pr = pr

    def compose(self) -> ComposeResult:
        yield Markdown(id="conversation")

    @property
    def conversation(self) -> Markdown:
        return self.query_one("#conversation", Markdown)

    @work
    async def render_conversation(self, conversation):
        log(f"Conversation: {conversation}")
        self.conversation.update(conversation)

    @work(thread=True)
    def fetch_conversation(self):
        # TODO: Okay, so the review API in Github is weird. There are 3 APIs we might need to leverage here.
        #
        # 1. The conversation API, which contains comments that happen separately from a review. Unclear if these
        # actually show up for PRs or if they're only actually present on issues (need to find an example).
        # 2. The reviews API, which returns distinct reviews and the comments that accompany them. This will be
        # necessary to setup a list of distinct threads of a review conversation that are happening.
        # 3. The review comments API, which pulls comments for a particular review. It doesn't look like the reviews API
        # actually has the full conversation associated with a review, so might need to query this as well :(
        conversation = g.get_conversation(self.pr)
        reviews = g.get_reviews(self.pr)
        log(f"Reviews: {reviews}")
        self.render_conversation(conversation)

    def on_mount(self) -> None:
        self.fetch_conversation()
