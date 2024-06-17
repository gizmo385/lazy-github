from github.PullRequest import PullRequest
from textual import log
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Footer,
    TabbedContent,
)

from lazy_github.lib.messages import PullRequestSelected, RepoSelected
from lazy_github.ui.widgets.actions import ActionsContainer
from lazy_github.ui.widgets.command_log import CommandLogSection
from lazy_github.ui.widgets.common import LazyGithubContainer
from lazy_github.ui.widgets.issues import IssuesContainer
from lazy_github.ui.widgets.pull_requests import (
    PrConversationTabPane,
    PrDiffTabPane,
    PrOverviewTabPane,
    PullRequestsContainer,
)
from lazy_github.ui.widgets.repositories import ReposContainer


class CurrentlySelectedRepo(Widget):
    current_repo_name: reactive[str | None] = reactive(None)

    def render(self):
        if self.current_repo_name:
            return f"Current repo: [green]{self.current_repo_name}[/green]"
        else:
            return "No repository selected"


class LazyGithubStatusSummary(Container):
    DEFAULT_CSS = """
    LazyGithubStatusSummary {
        height: 10%;
        width: 100%;
        border: solid $secondary;
    }
    """

    def compose(self):
        yield CurrentlySelectedRepo()


class LazyGithubFooter(Footer):
    pass


class SelectionDetailsContainer(LazyGithubContainer):
    DEFAULT_CSS = """
    SelectionDetailsContainer {
        height: 90%;
        dock: right;
    }
    SelectionDetailsContainer:focus-within {
        height: 80%;
    }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "[5] Details"
        yield TabbedContent(id="selection_detail_tabs")

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
        self.pull_requests.post_message(message)
        self.issues.post_message(message)
        self.actions.post_message(message)


class SelectionDetailsPane(Container):
    def compose(self) -> ComposeResult:
        yield SelectionDetailsContainer(id="selection_details")
        yield CommandLogSection()


class MainViewPane(Container):
    BINDINGS = [
        ("1", "focus_section('#repos_table')"),
        ("2", "focus_section('#pull_requests_table')"),
        ("3", "focus_section('#issues_table')"),
        ("4", "focus_section('#actions_table')"),
        # ("5", "focus_section('#scratch_space_tabs')"),
        ("6", "focus_section('LazyGithubCommandLog')"),
    ]

    def action_focus_section(self, selector: str) -> None:
        self.query_one(selector).focus()

    def compose(self) -> ComposeResult:
        yield SelectionsPane()
        yield SelectionDetailsPane()

    def on_pull_request_selected(self, message: PullRequestSelected) -> None:
        log(f"raw PR = {message.pr.raw_data}")
        tabbed_content = self.query_one("#selection_detail_tabs", TabbedContent)
        tabbed_content.clear_panes()
        tabbed_content.add_pane(PrOverviewTabPane(message.pr))
        tabbed_content.add_pane(PrDiffTabPane(message.pr))
        tabbed_content.add_pane(PrConversationTabPane(message.pr))
        tabbed_content.focus()


class LazyGithubMainScreen(Screen):
    BINDINGS = [("r", "refresh_repos", "Refresh global repo state")]

    def compose(self):
        with Container():
            yield LazyGithubStatusSummary()
            yield MainViewPane()
            yield LazyGithubFooter()
