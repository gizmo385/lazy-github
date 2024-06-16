from github.PullRequest import PullRequest
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, RichLog, TabPane

import lazy_github.lib.github as g
from lazy_github.lib.constants import IS_FAVORITED
from lazy_github.lib.messages import RepoSelected
from lazy_github.ui.widgets.command_log import log_event
from lazy_github.ui.widgets.common import LazyGithubContainer, LazyGithubDataTable


class PullRequestsContainer(LazyGithubContainer):
    """
    This container includes the primary datatable for viewing pull requests on the UI.
    """

    def compose(self) -> ComposeResult:
        self.border_title = "[2] Pull Requests"
        yield LazyGithubDataTable(id="pull_requests_table")

    @property
    def table(self) -> LazyGithubDataTable:
        return self.query_one("#pull_requests_table", LazyGithubDataTable)

    def on_mount(self):
        self.table.cursor_type = "row"
        self.table.add_column(IS_FAVORITED, key="favorite")
        self.table.add_column("Status", key="status")
        self.table.add_column("Number", key="number")
        self.table.add_column("Title", key="title")

    async def on_repo_selected(self, message: RepoSelected) -> None:
        # TODO: Load the PRs for the selected repo
        message.stop()

    @work()
    async def select_pull_request(self, pr: PullRequest) -> str:
        log_event(f"Selected PR {pr}")
        # scratch_space = self.app.query_one(ScratchSpaceContainer)
        # scratch_space.show_pr_details(pr)

    @work
    async def get_selected_pr(self) -> PullRequest:
        pass

    @on(LazyGithubDataTable.RowSelected, "#repos_table")
    async def pr_selected(self):
        # Bubble a message up indicating that a repo was selected
        pr = await self.get_selected_pr()
        log_event(f"Selected PR {pr.title}")


class PrOverviewTabPane(TabPane):
    def __init__(self, pr: PullRequest) -> None:
        super().__init__("Overview", id="overview")
        self.pr = pr

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                yield Label(f"[b]{self.pr.title}[/b]", id="pr_title")
                yield Label(f"{self.pr.head.ref} --{self.pr.commits}--> {self.pr.base.ref}")
            yield Label(f"[b]Description[/b]: {self.pr.body}", id="pr_description")


class PrDiffTabPane(TabPane):
    def __init__(self, pr: PullRequest) -> None:
        super().__init__("Diff", id="diff_pane")
        self.pr = pr

    def compose(self) -> ComposeResult:
        yield RichLog(id="diff_contents", highlight=True)

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
        super().__init__("Conversation", id="conversation")
        self.pr = pr

    def compose(self) -> ComposeResult:
        yield Label("Conversation")
