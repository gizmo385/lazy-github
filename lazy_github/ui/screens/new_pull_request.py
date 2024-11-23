from textual import on, suggester, validation, work
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Markdown, Rule, Switch, TextArea

from lazy_github.lib.bindings import LazyGithubBindings
from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.github.branches import list_branches
from lazy_github.lib.github.pull_requests import create_pull_request
from lazy_github.lib.messages import PullRequestCreated
from lazy_github.models.github import Branch, FullPullRequest


class BranchesLoaded(Message):
    def __init__(self, branches: list[Branch]) -> None:
        super().__init__()
        self.branches = branches


class BranchesSelected(Message):
    def __init__(self, head_ref: str, base_ref: str) -> None:
        super().__init__()
        self.head_ref = head_ref
        self.base_ref = base_ref


class BranchSelection(Horizontal):
    DEFAULT_CSS = """
    BranchSelection {
        width: 100%;
        height: auto;
    }
    
    Label {
        padding-top: 1;
    }

    Input {
        width: 30%;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.branches: dict[str, Branch] = {}

    def compose(self) -> ComposeResult:
        assert LazyGithubContext.current_repo is not None, "Unexpectedly missing current repo in new PR modal"
        non_empty_validator = validation.Length(minimum=1)
        yield Label("[bold]Base[/bold]")
        yield Input(
            id="base_ref",
            placeholder="Choose a base ref",
            value=LazyGithubContext.current_repo.default_branch,
            validators=[non_empty_validator],
        )
        yield Label(":left_arrow: [bold]Compare[/bold]")
        yield Input(id="head_ref", placeholder="Choose a head ref", validators=[non_empty_validator])
        yield Label("Draft")
        yield Switch(id="pr_is_draft", value=False)

    @property
    def _head_ref_input(self) -> Input:
        return self.query_one("#head_ref", Input)

    @property
    def _base_ref_input(self) -> Input:
        return self.query_one("#base_ref", Input)

    @property
    def head_ref(self) -> str:
        return self._head_ref_input.value

    @property
    def base_ref(self) -> str:
        return self._base_ref_input.value

    async def on_mount(self) -> None:
        self.fetch_branches()

    @on(BranchesLoaded)
    def handle_loaded_branches(self, message: BranchesLoaded) -> None:
        self.branches = {b.name: b for b in message.branches}
        branch_suggester = suggester.SuggestFromList(self.branches.keys())
        self._head_ref_input.suggester = branch_suggester
        self._base_ref_input.suggester = branch_suggester

    @work
    async def fetch_branches(self) -> None:
        # This shouldn't happen since the current repo needs to be set to open this modal, but we'll validate it to
        # make sure
        assert LazyGithubContext.current_repo is not None, "Current repo unexpectedly missing in new PR modal"

        branches = await list_branches(LazyGithubContext.current_repo)
        self.post_message(BranchesLoaded(branches))


class NewPullRequestButtons(Horizontal):
    DEFAULT_CSS = """
    NewPullRequestButtons {
        align: center middle;
        height: auto;
        width: 100%;
    }
    Button {
        margin: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Button("Create", id="submit_new_pr", variant="success")
        yield Button("Cancel", id="cancel_new_pr", variant="error")


class NewPullRequestContainer(VerticalScroll):
    DEFAULT_CSS = """
    NewPullRequestContainer {
        padding: 1;
    }
    Horizontal {
        content-align: center middle;
    }

    #pr_description {
        height: 10;
        width: 100%;
        margin-bottom: 1;
    }

    #pr_title {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Markdown("# New Pull Request (WIP)")
        yield BranchSelection()
        yield Rule()
        yield Label("[bold]Pull Request Title[/bold]")
        yield Input(id="pr_title", placeholder="Title", validators=[validation.Length(minimum=1)])
        yield Label("[bold]Pull Request Description[/bold]")
        yield TextArea.code_editor(id="pr_description")
        yield NewPullRequestButtons()

    @on(Button.Pressed, "#cancel_new_pr")
    def cancel_pull_request(self, _: Button.Pressed):
        self.app.pop_screen()

    @on(Button.Pressed, "#submit_new_pr")
    async def submit_pull_request(self, _: Button.Pressed):
        assert LazyGithubContext.current_repo is not None, "Unexpectedly missing current repo in new PR modal"
        title_field = self.query_one("#pr_title", Input)
        title_field.validate(title_field.value)
        description_field = self.query_one("#pr_description", TextArea)
        head_ref_field = self.query_one("#head_ref", Input)
        head_ref_field.validate(head_ref_field.value)
        base_ref_field = self.query_one("#base_ref", Input)
        base_ref_field.validate(base_ref_field.value)
        draft_field = self.query_one("#pr_is_draft", Switch)

        if not (title_field.is_valid and head_ref_field.is_valid and base_ref_field.is_valid):
            self.notify("Missing required fields!", title="Invalid PR!", severity="error")
            return

        self.notify("Creating new pull request...")
        try:
            created_pr = await create_pull_request(
                LazyGithubContext.current_repo,
                title_field.value,
                description_field.text,
                base_ref_field.value,
                head_ref_field.value,
                draft=draft_field.value,
            )
        except Exception:
            self.notify(
                "Check that your branches are valid and that a PR does not already exist",
                title="Error creating pull request",
                severity="error",
            )
        else:
            self.notify("Successfully created PR!")
            self.post_message(PullRequestCreated(created_pr))


class NewPullRequestModal(ModalScreen[FullPullRequest | None]):
    DEFAULT_CSS = """
    NewPullRequestModal {
        border: ascii green;
        align: center middle;
        content-align: center middle;
    }

    NewPullRequestContainer {
        width: 100;
        height: auto;
        border: thick $background 80%;
        background: $surface-lighten-3;
        margin: 1;
    }
    """

    BINDINGS = [LazyGithubBindings.CANCEL_DIALOG]

    def compose(self) -> ComposeResult:
        yield NewPullRequestContainer()

    def action_cancel(self) -> None:
        self.dismiss(None)

    @on(PullRequestCreated)
    def on_pull_request_created(self, message: PullRequestCreated) -> None:
        self.dismiss(message.pull_request)
