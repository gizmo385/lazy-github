from functools import partial
from typing import NamedTuple

from httpx import HTTPError
from textual import work
from textual.app import ComposeResult
from textual.command import Hit, Hits, Provider
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import Screen
from textual.types import IgnoreReturnCallbackType
from textual.widget import Widget
from textual.widgets import Footer, TabbedContent

from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.logging import lg
from lazy_github.lib.github.issues import list_issues
from lazy_github.lib.github.pull_requests import get_full_pull_request
from lazy_github.lib.messages import (
    IssuesAndPullRequestsFetched,
    IssueSelected,
    PullRequestSelected,
    RepoSelected,
)
from lazy_github.models.github import Repository
from lazy_github.ui.screens.new_issue import NewIssueModal
from lazy_github.ui.screens.new_pull_request import NewPullRequestModal
from lazy_github.ui.screens.settings import SettingsModal
from lazy_github.ui.widgets.command_log import CommandLogSection
from lazy_github.ui.widgets.common import LazyGithubContainer
from lazy_github.ui.widgets.info import LazyGithubInfoTabPane
from lazy_github.ui.widgets.issues import IssueConversationTabPane, IssueOverviewTabPane, IssuesContainer, issue_to_cell
from lazy_github.ui.widgets.pull_requests import (
    PrConversationTabPane,
    PrDiffTabPane,
    PrOverviewTabPane,
    PullRequestsContainer,
    pull_request_to_cell,
)
from lazy_github.ui.widgets.repositories import ReposContainer
from lazy_github.ui.widgets.workflows import WorkflowsContainer


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
        max-height: 3;
        width: 100%;
        border: solid $secondary;
    }
    """

    def compose(self):
        yield CurrentlySelectedRepo(id="currently_selected_repo")


class SelectionDetailsContainer(LazyGithubContainer):
    DEFAULT_CSS = """
    SelectionDetailsContainer {
        max-height: 100%;
        dock: right;
    }
    SelectionDetailsContainer:focus-within {
        max-height: 100%;
        min-height: 80%;
        dock: right;
    }
    """

    BINDINGS = [("j", "scroll_tab_down"), ("k", "scroll_tab_up")]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tabs = TabbedContent(id="selection_detail_tabs")

    def compose(self) -> ComposeResult:
        self.border_title = "[5] Details"
        yield self.tabs

    def on_mount(self) -> None:
        self.tabs.add_pane(LazyGithubInfoTabPane())
        pass

    def action_scroll_tab_down(self) -> None:
        if self.tabs.active_pane:
            self.tabs.active_pane.scroll_down()

    def action_scroll_tab_up(self) -> None:
        if self.tabs.active_pane:
            self.tabs.active_pane.scroll_up()


class SelectionsPane(Container):
    BINDINGS = [
        ("I", "open_issue", "Open new issue"),
        ("P", "open_pull_request", "Open new pull request"),
    ]
    DEFAULT_CSS = """
    SelectionsPane {
        height: 100%;
        width: 40%;
        dock: left;
    }
    """

    def compose(self) -> ComposeResult:
        yield ReposContainer(id="repos")
        pulls = PullRequestsContainer(id="pull_requests")
        pulls.display = LazyGithubContext.config.appearance.show_pull_requests
        yield pulls

        issues = IssuesContainer(id="issues")
        issues.display = LazyGithubContext.config.appearance.show_issues
        yield issues

        workflows = WorkflowsContainer(id="workflows")
        workflows.display = LazyGithubContext.config.appearance.show_workflows
        yield workflows

    def update_displayed_sections(self) -> None:
        lg.debug("Updating displayed UI components after settings update")
        self.pull_requests.display = LazyGithubContext.config.appearance.show_pull_requests
        self.issues.display = LazyGithubContext.config.appearance.show_issues
        self.workflows.display = LazyGithubContext.config.appearance.show_workflows

    def action_open_issue(self) -> None:
        self.trigger_issue_creation_flow()

    @work
    async def trigger_issue_creation_flow(self) -> None:
        if LazyGithubContext.current_repo is None:
            self.notify("Please select a repository first!", title="Cannot open new pull request", severity="error")
            return

        if new_issue := await self.app.push_screen_wait(NewIssueModal()):
            self.issues.searchable_table.append_rows([issue_to_cell(new_issue)])
            self.issues.issues[new_issue.number] = new_issue

    async def action_open_pull_request(self) -> None:
        self.trigger_pr_creation_flow()

    @work
    async def trigger_pr_creation_flow(self) -> None:
        if LazyGithubContext.current_repo is None:
            self.notify("Please select a repository first!", title="Cannot open new pull request", severity="error")
            return

        if new_pr := await self.app.push_screen_wait(NewPullRequestModal()):
            self.pull_requests.searchable_table.append_rows([pull_request_to_cell(new_pr)])
            self.pull_requests.pull_requests[new_pr.number] = new_pr

    @property
    def pull_requests(self) -> PullRequestsContainer:
        return self.query_one("#pull_requests", PullRequestsContainer)

    @property
    def issues(self) -> IssuesContainer:
        return self.query_one("#issues", IssuesContainer)

    @property
    def workflows(self) -> WorkflowsContainer:
        return self.query_one("#workflows", WorkflowsContainer)

    @work
    async def fetch_issues_and_pull_requests(self, repo: Repository) -> None:
        state_filter = LazyGithubContext.config.issues.state_filter
        owner_filter = LazyGithubContext.config.issues.owner_filter
        try:
            issues_and_pull_requests = await list_issues(repo, state_filter, owner_filter)
        except HTTPError:
            lg.exception("Error fetching issues and PRs from Github API")
        else:
            issue_and_pr_message = IssuesAndPullRequestsFetched(issues_and_pull_requests)
            self.pull_requests.post_message(issue_and_pr_message)
            self.issues.post_message(issue_and_pr_message)

    async def on_repo_selected(self, message: RepoSelected) -> None:
        LazyGithubContext.current_repo = message.repo
        if self.pull_requests.display or self.issues.display:
            self.fetch_issues_and_pull_requests(message.repo)
        if self.workflows.display:
            self.workflows.load_repo(message.repo)


class SelectionDetailsPane(Container):
    def compose(self) -> ComposeResult:
        yield SelectionDetailsContainer(id="selection_details")
        command_log_section = CommandLogSection(id="command_log")
        command_log_section.display = LazyGithubContext.config.appearance.show_command_log
        yield command_log_section


class MainViewPane(Container):
    BINDINGS = [
        ("1", "focus_section('#repos_table')"),
        ("2", "focus_section('#pull_requests_table')"),
        ("3", "focus_section('#issues_table')"),
        # ("4", "focus_section('#actions_table')"),
        ("4", "focus_workflow_tabs"),
        ("5", "focus_tabs"),
        ("6", "focus_section('LazyGithubCommandLog')"),
    ]

    def action_focus_section(self, selector: str) -> None:
        self.query_one(selector).focus()

    def action_focus_workflow_tabs(self) -> None:
        tabs = self.query_one("#workflow_tabs", TabbedContent)
        if tabs.children and tabs.tab_count > 0:
            tabs.children[0].focus()

    def action_focus_tabs(self) -> None:
        tabs = self.query_one("#selection_detail_tabs", TabbedContent)
        if tabs.children and tabs.tab_count > 0:
            tabs.children[0].focus()

    def compose(self) -> ComposeResult:
        yield SelectionsPane(id="selections_pane")
        yield SelectionDetailsPane(id="details_pane")

    @property
    def details(self) -> SelectionDetailsContainer:
        return self.query_one("#selection_details", SelectionDetailsContainer)

    async def on_pull_request_selected(self, message: PullRequestSelected) -> None:
        full_pr = await get_full_pull_request(message.pr)
        tabbed_content = self.query_one("#selection_detail_tabs", TabbedContent)
        await tabbed_content.clear_panes()
        await tabbed_content.add_pane(PrOverviewTabPane(full_pr))
        await tabbed_content.add_pane(PrDiffTabPane(full_pr))
        await tabbed_content.add_pane(PrConversationTabPane(full_pr))
        tabbed_content.children[0].focus()
        self.details.border_title = f"[5] PR #{full_pr.number} Details"

    async def on_issue_selected(self, message: IssueSelected) -> None:
        tabbed_content = self.query_one("#selection_detail_tabs", TabbedContent)
        await tabbed_content.clear_panes()
        await tabbed_content.add_pane(IssueOverviewTabPane(message.issue))
        await tabbed_content.add_pane(IssueConversationTabPane(message.issue))
        tabbed_content.children[0].focus()
        self.details.border_title = f"[5] Issue #{message.issue.number} Details"


class LazyGithubCommand(NamedTuple):
    name: str
    action: IgnoreReturnCallbackType
    help_text: str


class MainScreenCommandProvider(Provider):
    @property
    def commands(self) -> tuple[LazyGithubCommand, ...]:
        assert isinstance(self.screen, LazyGithubMainScreen)

        toggle_ui = self.screen.action_toggle_ui

        _commands: list[LazyGithubCommand] = [
            LazyGithubCommand(
                "Toggle Command Log", partial(toggle_ui, "command_log"), "Toggle showing or hiding the command log"
            ),
            LazyGithubCommand(
                "Toggle Workflows", partial(toggle_ui, "actions"), "Toggle showing or hiding repo actions"
            ),
            LazyGithubCommand("Toggle Issues", partial(toggle_ui, "issues"), "Toggle showing or hiding repo issues"),
            LazyGithubCommand(
                "Toggle Pull Requests",
                partial(toggle_ui, "pull_requests"),
                "Toggle showing or hiding repo pull requests",
            ),
            LazyGithubCommand("Change Settings", self.screen.action_show_settings_modal, "Adjust LazyGithub settings"),
        ]
        return tuple(_commands)

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        for command in self.commands:
            if (match := matcher.match(command.name)) > 0:
                yield Hit(
                    match,
                    matcher.highlight(command.name),
                    command.action,
                    help=command.help_text,
                )


class LazyGithubMainScreen(Screen):
    COMMANDS = {MainScreenCommandProvider}

    def compose(self):
        with Container():
            yield LazyGithubStatusSummary()
            yield MainViewPane()
            yield Footer()

    async def action_toggle_ui(self, ui_to_hide: str):
        widget = self.query_one(f"#{ui_to_hide}", Widget)
        widget.display = not widget.display

    async def action_show_settings_modal(self) -> None:
        self.app.push_screen(SettingsModal())

    def handle_settings_update(self) -> None:
        self.query_one("#selections_pane", SelectionsPane).update_displayed_sections()

    def on_repo_selected(self, message: RepoSelected) -> None:
        self.query_one("#currently_selected_repo", CurrentlySelectedRepo).current_repo_name = message.repo.full_name
