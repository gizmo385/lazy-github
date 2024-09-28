from textual import on
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Input, Label, Markdown, Rule, Select, TextArea


class BranchSelection(Horizontal):
    DEFAULT_CSS = """
    BranchSelection {
        width: 100%;
        height: auto;
    }
    
    Label {
        padding-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("[bold]Base[/bold]")
        yield Select(id="base_ref", prompt="Choose a base ref", options=[("main", "main")])
        yield Label(":left_arrow: [bold]Compare[/bold]")
        yield Select(id="head_ref", prompt="Choose a head ref", options=[("main", "main")])

    @property
    def head_ref(self) -> str:
        return str(self.query_one("#head_ref", Select).value)

    @property
    def base_ref(self) -> str:
        return str(self.query_one("#base_ref", Select).value)


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

    #pr_diff {
        height: auto;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Markdown("# New Pull Request (WIP)")
        yield BranchSelection()
        yield Rule()
        yield Label("[bold]Pull Request Title[/bold]")
        yield Input(id="pr_title", placeholder="Title")
        yield Label("[bold]Pull Request Description[/bold]")
        yield TextArea(id="pr_description")
        yield NewPullRequestButtons()
        yield Label("Changes:")
        yield TextArea(id="pr_diff", disabled=True)

    @on(Button.Pressed, "#cancel_new_pr")
    def cancel_pull_request(self, _: Button.Pressed):
        self.app.pop_screen()

    def fetch_branches(self) -> None:
        # TODO: Fetch the branches from the remote repo that can be loaded
        pass


class NewPullRequestModal(ModalScreen):
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

    BINDINGS = [("ESC, q", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        yield NewPullRequestContainer()

    def action_cancel(self) -> None:
        self.dismiss()
