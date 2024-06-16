from datetime import datetime
from typing import List, Optional

from github.PullRequest import PullRequest
from github.Repository import Repository
from textual import log, on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.coordinate import Coordinate
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Footer,
    Label,
    Markdown,
    RichLog,
    TabbedContent,
    TabPane,
)

import lazy_github.lib.github as g
from lazy_github.lib.constants import IS_FAVORITED, IS_NOT_FAVORITED, IS_PRIVATE, IS_PUBLIC
from lazy_github.ui.widgets.command_log import CommandLogSection, log_event
from lazy_github.ui.widgets.common import LazyGithubContainer, LazyGithubDataTable

# Color palletes
# https://coolors.co/84ffc9-aab2ff-eca0ff


class RepoSelected(Message):
    def __init__(self, repo: Repository) -> None:
        self.repo = repo
        super().__init__()


class ReposContainer(LazyGithubContainer):
    BINDINGS = [
        ("f", "toggle_favorite_repo", "Toggle favorite"),
        ("enter", "select"),
    ]

    favorite_column_index: int = -1
    owner_column_index: int = 1
    name_column_index: int = 1
    private_column_index: int = 1

    def compose(self) -> ComposeResult:
        self.border_title = "[1] Repositories"
        yield LazyGithubDataTable(id="repos_table")

    @property
    def table(self) -> LazyGithubDataTable:
        return self.query_one("#repos_table", LazyGithubDataTable)

    async def on_mount(self) -> None:
        # Setup the table
        self.table.cursor_type = "row"
        self.table.add_column(IS_FAVORITED, key="favorite")
        self.table.add_column("Owner", key="owner")
        self.table.add_column("Name", key="name")
        self.table.add_column("Private", key="private")

        self.favorite_column_index = self.table.get_column_index("favorite")
        self.owner_column_index = self.table.get_column_index("owner")
        self.name_column_index = self.table.get_column_index("name")
        self.private_column_index = self.table.get_column_index("private")

        # Let the UI load, then trigger this as a callback
        self.set_timer(0.1, self.load_repos)

    async def get_selected_repo(self) -> Repository:
        current_row = self.table.cursor_row
        owner = self.table.get_cell_at(Coordinate(current_row, self.owner_column_index))
        repo_name = self.table.get_cell_at(Coordinate(current_row, self.name_column_index))
        return g.github_client().get_repo(f"{owner}/{repo_name}")

    @work
    async def add_repos_to_table(self, repos: List[Repository]) -> None:
        rows = []
        for repo in repos:
            rows.append(
                [
                    IS_NOT_FAVORITED,
                    repo.owner.login,
                    repo.name,
                    IS_PRIVATE if repo.private else IS_PUBLIC,
                ]
            )
        self.table.add_rows(rows)

    @work(thread=True)
    def load_repos(self) -> None:
        user = g.github_client().get_user()
        repos = user.get_repos()
        self.add_repos_to_table(repos)

    async def action_toggle_favorite_repo(self):
        repo = await self.get_selected_repo()
        log_event(f"Favoriting repo {repo.full_name}")

    @on(LazyGithubDataTable.RowSelected, "#repos_table")
    async def repo_selected(self):
        # Bubble a message up indicating that a repo was selected
        repo = await self.get_selected_repo()
        self.post_message(RepoSelected(repo))
        log_event(f"Selected repo {repo.full_name}")


class PullRequestsContainer(LazyGithubContainer):
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
        scratch_space = self.app.query_one(ScratchSpaceContainer)
        scratch_space.show_pr_details(pr)

    @work
    async def get_selected_pr(self) -> PullRequest:
        pass

    @on(LazyGithubDataTable.RowSelected, "#repos_table")
    async def pr_selected(self):
        # Bubble a message up indicating that a repo was selected
        pr = await self.get_selected_pr()
        log_event(f"Selected PR {pr.title}")


class IssuesContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[3] Issues"
        yield LazyGithubDataTable(id="pull_requests_table")

    async def on_repo_selected(self, message: RepoSelected) -> None:
        # TODO: Load the issues for the selected repo
        message.stop()


class ActionsContainer(LazyGithubContainer):
    def compose(self) -> ComposeResult:
        self.border_title = "[4] Actions"
        yield LazyGithubDataTable(id="actions_table")

    async def on_repo_selected(self, message: RepoSelected) -> None:
        # TODO: Load the actions for the selected repo
        message.stop()


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


class ScratchSpaceContainer(LazyGithubContainer):
    DEFAULT_CSS = """
    ScratchSpaceContainer {
        height: 90%;
        dock: right;
    }
    ScratchSpaceContainer:focus-within {
        height: 80%;
    }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "[5] Details"
        yield TabbedContent(id="scratch_space_tabs")

    def show_pr_details(self, pr: PullRequest) -> None:
        # Update the tabs to show the PR details
        tabbed_content: TabbedContent = self.query_one("#scratch_space_tabs")
        log(f"raw PR = {pr.raw_data}")
        tabbed_content.clear_panes()
        tabbed_content.add_pane(PrOverviewTabPane(pr))
        tabbed_content.add_pane(PrDiffTabPane(pr))
        tabbed_content.add_pane(PrConversationTabPane(pr))
        tabbed_content.focus()


class SelectionsPane(Container):
    DEFAULT_CSS = """
    SelectionsPane {
        height: 100%;
        width: 40%;
        dock: left;
    }
    """

    def compose(self) -> ComposeResult:
        yield ReposContainer(id="repos")
        yield PullRequestsContainer(id="pull_requests")
        yield IssuesContainer(id="issues")
        yield ActionsContainer(id="actions")

    @property
    def pull_requests(self) -> PullRequestsContainer:
        return self.query_one("#pull_requests", PullRequestsContainer)

    @property
    def issues(self) -> IssuesContainer:
        return self.query_one("#issues", IssuesContainer)

    @property
    def actions(self) -> ActionsContainer:
        return self.query_one("#actions", ActionsContainer)

    async def on_repo_selected(self, message: RepoSelected) -> None:
        message.stop()
        self.pull_requests.post_message(message)
        self.issues.post_message(message)
        self.actions.post_message(message)


class DetailsPane(Container):
    def compose(self) -> ComposeResult:
        yield ScratchSpaceContainer(id="Scratch")
        yield CommandLogSection()


class MainViewPane(Container):
    BINDINGS = [
        # ("1", "focus_section('ReposOptionsList')"),
        # ("2", "focus_section('PullRequestsOptionsList')"),
        # ("3", "focus_section('IssuesOptionList')"),
        # ("4", "focus_section('ActionsOptionList')"),
        # ("5", "focus_section('#scratch_space_tabs')"),
        # ("6", "focus_section('LazyGithubCommandLog')"),
    ]

    def action_focus_section(self, selector: str) -> None:
        self.query_one(selector).focus()

    def compose(self) -> ComposeResult:
        yield SelectionsPane()
        yield DetailsPane()


class CurrentlySelectedRepo(Widget):
    current_repo_name: reactive[str | None] = reactive(None)

    def render(self):
        if self.current_repo_name:
            return f"Current repo: [green]{self.current_repo_name}[/green]"
        else:
            return "No repository selected"


class LazyGithubHeader(Container):
    DEFAULT_CSS = """
    LazyGithubHeader {
        height: 10%;
        width: 100%;
        border: solid $secondary;
    }
    """

    def compose(self):
        yield CurrentlySelectedRepo()


class LazyGithubFooter(Footer):
    pass


class LazyGithubMainScreen(Screen):
    BINDINGS = [("r", "refresh_repos", "Refresh global repo state")]

    def compose(self):
        with Container():
            yield LazyGithubHeader()
            yield MainViewPane()
            yield LazyGithubFooter()
