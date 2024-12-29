from textual import on, suggester, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, Input, Label, Markdown

from lazy_github.lib.bindings import LazyGithubBindings
from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.github.branches import list_branches
from lazy_github.lib.github.workflows import create_dispatch_event
from lazy_github.lib.messages import BranchesLoaded
from lazy_github.models.github import Workflow
from lazy_github.ui.widgets.common import LazyGithubFooter


class TriggerWorkflowButtons(Horizontal):
    DEFAULT_CSS = """
    TriggerWorkflowButtons {
        align: center middle;
        height: auto;
        width: 100%;
    }
    Button {
        margin: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Button("Trigger", id="trigger", variant="success")
        yield Button("Cancel", id="cancel", variant="error")


class TriggerWorkflowContainer(Container):
    DEFAULT_CSS = """
    TriggerWorkflowContainer {
        align: center middle;
    }
    """

    def __init__(self, workflow: Workflow) -> None:
        super().__init__()
        self.workflow = workflow

    def compose(self) -> ComposeResult:
        assert LazyGithubContext.current_repo is not None, "Unexpectedly missing current repo in trigger workflow modal"
        yield Markdown(f"# Triggering workflow: {self.workflow.name}")
        yield Label("[bold]Branch[/bold]")
        yield Input(
            id="branch_to_build",
            placeholder="Choose a branch",
            validators=Length(minimum=1),
            value=LazyGithubContext.current_repo.default_branch,
        )
        yield TriggerWorkflowButtons()

    @on(BranchesLoaded)
    def handle_loaded_branches(self, message: BranchesLoaded) -> None:
        self.branches = {b.name: b for b in message.branches}
        branch_suggester = suggester.SuggestFromList(self.branches.keys())
        self.query_one("#branch_to_build", Input).suggester = branch_suggester

    @work
    async def fetch_branches(self) -> None:
        # This shouldn't happen since the current repo needs to be set to open this modal, but we'll validate it to
        # make sure
        assert LazyGithubContext.current_repo is not None, "Current repo unexpectedly missing in new PR modal"

        branches = await list_branches(LazyGithubContext.current_repo)
        self.post_message(BranchesLoaded(branches))

    async def on_mount(self) -> None:
        self.fetch_branches()


class TriggerWorkflowModal(ModalScreen[bool]):
    DEFAULT_CSS = """
    TriggerWorkflowModal {
        align: center middle;
        content-align: center middle;
    }

    TriggerWorkflowContainer {
        width: 60;
        max-height: 20;
        border: thick $background 80%;
        background: $surface-lighten-3;
    }
    """

    BINDINGS = [LazyGithubBindings.SUBMIT_DIALOG, LazyGithubBindings.CLOSE_DIALOG]

    def __init__(self, workflow: Workflow) -> None:
        super().__init__()
        self.workflow = workflow

    def compose(self) -> ComposeResult:
        yield TriggerWorkflowContainer(self.workflow)
        yield LazyGithubFooter()

    @on(Button.Pressed, "#trigger")
    async def action_submit(self) -> None:
        assert LazyGithubContext.current_repo is not None, "Unexpectedly missing current repo!"
        branch_input = self.query_one("#branch_to_build", Input)
        branch_input.validate(branch_input.value)
        if branch_input.is_valid:
            if await create_dispatch_event(LazyGithubContext.current_repo, self.workflow, branch_input.value):
                self.dismiss(True)
            else:
                self.notify(
                    "Could not trigger build - are you sure this workflow supports dispatch events?",
                    title="Error Triggering Build",
                    severity="error",
                )
        else:
            self.notify("You must enter a branch!", title="Validation Error", severity="error")

    @on(Button.Pressed, "#cancel")
    async def action_close(self) -> None:
        self.dismiss(False)
