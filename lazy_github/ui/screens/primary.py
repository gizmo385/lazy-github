from functools import partial
from typing import NamedTuple

from httpx import HTTPStatusError
from textual.app import ComposeResult
from textual.command import Hit, Hits, Provider
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import Screen
from textual.types import IgnoreReturnCallbackType
from textual.widget import Widget
from textual.widgets import Footer, TabbedContent

from lazy_github.lib.github.client import GithubClient
from lazy_github.lib.github.issues import list_issues
from lazy_github.lib.github.pull_requests import get_full_pull_request
from lazy_github.lib.messages import IssuesAndPullRequestsFetched, IssueSelected, PullRequestSelected, RepoSelected
from lazy_github.ui.screens.settings import SettingsModal
from lazy_github.ui.widgets.actions import ActionsContainer
from lazy_github.ui.widgets.command_log import CommandLogSection
from lazy_github.ui.widgets.common import LazyGithubContainer
from lazy_github.ui.widgets.issues import IssueConversationTabPane, IssueOverviewTabPane, IssuesContainer
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
        max-height: 3;
        width: 100%;
        border: solid $secondary;
    }
    """

    def compose(self):
        yield CurrentlySelectedRepo(id="currently_selected_repo")


class LazyGithubFooter(Footer):
    pass


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

    def compose(self) -> ComposeResult:
        self.border_title = "[5] Details"
        yield TabbedContent(id="selection_detail_tabs")

    @property
    def tabs(self) -> TabbedContent:
        return self.query_one("#selection_detail_tabs", TabbedContent)

    def action_scroll_tab_down(self) -> None:
        if self.tabs.active_pane:
            self.tabs.active_pane.scroll_down()

    def action_scroll_tab_up(self) -> None:
        if self.tabs.active_pane:
            self.tabs.active_pane.scroll_up()


class SelectionsPane(Container):
    DEFAULT_CSS = """
    SelectionsPane {
        height: 100%;
        width: 40%;
        dock: left;
    }
    """

    def __init__(self, client: GithubClient, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.client = client

    def compose(self) -> ComposeResult:
        yield ReposContainer(self.client, id="repos")
        pulls = PullRequestsContainer(self.client, id="pull_requests")
        pulls.display = self.client.config.appearance.show_pull_requests
        yield pulls

        issues = IssuesContainer(id="issues")
        issues.display = self.client.config.appearance.show_issues
        yield issues

        actions = ActionsContainer(id="actions")
        actions.display = self.client.config.appearance.show_actions
        yield actions

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
        # self.actions.post_message(message)
        try:
            state_filter = self.client.config.issues.state_filter
            owner_filter = self.client.config.issues.owner_filter
            issues_and_pull_requests = []
            if self.pull_requests.display or self.issues.display:
                issues_and_pull_requests = await list_issues(self.client, message.repo, state_filter, owner_filter)
        except HTTPStatusError as hse:
            if hse.response.status_code == 404:
                pass
            else:
                raise
        else:
            issue_and_pr_message = IssuesAndPullRequestsFetched(issues_and_pull_requests)
            self.pull_requests.post_message(issue_and_pr_message)
            self.issues.post_message(issue_and_pr_message)


class SelectionDetailsPane(Container):
    def __init__(self, client: GithubClient, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.client = client

    def compose(self) -> ComposeResult:
        yield SelectionDetailsContainer(id="selection_details")
        command_log_section = CommandLogSection(id="command_log")
        command_log_section.display = self.client.config.appearance.show_command_log
        yield command_log_section


class MainViewPane(Container):
    BINDINGS = [
        ("1", "focus_section('#repos_table')"),
        ("2", "focus_section('#pull_requests_table')"),
        ("3", "focus_section('#issues_table')"),
        ("4", "focus_section('#actions_table')"),
        ("5", "focus_tabs"),
        ("6", "focus_section('LazyGithubCommandLog')"),
    ]

    def __init__(self, client: GithubClient, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.client = client

    def action_focus_section(self, selector: str) -> None:
        self.query_one(selector).focus()

    def action_focus_tabs(self) -> None:
        tabs = self.query_one("#selection_detail_tabs", TabbedContent)
        if tabs.children and tabs.tab_count > 0:
            tabs.children[0].focus()

    def compose(self) -> ComposeResult:
        yield SelectionsPane(self.client)
        yield SelectionDetailsPane(self.client)

    async def on_pull_request_selected(self, message: PullRequestSelected) -> None:
        full_pr = await get_full_pull_request(self.client, message.pr)
        tabbed_content = self.query_one("#selection_detail_tabs", TabbedContent)
        await tabbed_content.clear_panes()
        await tabbed_content.add_pane(PrOverviewTabPane(full_pr))
        await tabbed_content.add_pane(PrDiffTabPane(self.client, full_pr))
        await tabbed_content.add_pane(PrConversationTabPane(self.client, full_pr))
        tabbed_content.children[0].focus()

    async def on_issue_selected(self, message: IssueSelected) -> None:
        tabbed_content = self.query_one("#selection_detail_tabs", TabbedContent)
        await tabbed_content.clear_panes()
        await tabbed_content.add_pane(IssueOverviewTabPane(message.issue))
        await tabbed_content.add_pane(IssueConversationTabPane(self.client, message.issue))
        tabbed_content.children[0].focus()


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
            LazyGithubCommand("Toggle Actions", partial(toggle_ui, "actions"), "Toggle showing or hiding repo actions"),
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
    BINDINGS = [("r", "refresh_repos", "Refresh global repo state")]

    COMMANDS = {MainScreenCommandProvider}

    def __init__(self, client: GithubClient, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.client = client

    def compose(self):
        with Container():
            yield LazyGithubStatusSummary()
            yield MainViewPane(self.client)
            yield LazyGithubFooter()

    async def action_toggle_ui(self, ui_to_hide: str):
        widget = self.query_one(f"#{ui_to_hide}", Widget)
        widget.display = not widget.display

    async def action_show_settings_modal(self) -> None:
        self.app.push_screen(SettingsModal(self.client.config))

    def on_repo_selected(self, message: RepoSelected) -> None:
        self.query_one("#currently_selected_repo", CurrentlySelectedRepo).current_repo_name = message.repo.full_name
