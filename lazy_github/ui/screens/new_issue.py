from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Rule, TextArea

from lazy_github.lib.github import issues
from lazy_github.models.github import Repository


class NewIssueContainer(Container):
    DEFAULT_CSS = """
    #button_holder {
        align: center middle;
    }

    ScrollableContainer {
        height: 80%;
    }

    #new_issue_body {
        height: 15;
    }
    """

    def __init__(self, repo: Repository, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.repo = repo

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield Label("[bold]Title[/bold]")
            yield Input(placeholder="Title", id="new_issue_title")

            yield Rule()

            yield Label("[bold]Description[/bold]")
            yield TextArea.code_editor(id="new_issue_body", soft_wrap=True)

        with Horizontal(id="button_holder"):
            yield Button("Save", id="save_new_issue", variant="success")
            yield Button("Cancel", id="cancel_new_issue", variant="error")

    @on(Button.Pressed, "#cancel_new_issue")
    def cancel_new_issue(self, _: Button) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#save_new_issue")
    async def submit_new_issue(self, _: Button) -> None:
        title = self.query_one("#new_issue_title", Input).value
        body = self.query_one("#new_issue_body", TextArea).text
        if not str(title):
            self.notify("Must have a non-empty issue title!", severity="error")
            return
        if not str(body):
            self.notify("Must have a non-empty issue body!", severity="error")
            return

        self.notify("Creating new issue...")
        new_issue = await issues.create_issue(self.repo, title, body)
        self.notify(f"Successfully updated created issue #{new_issue.number}")
        self.app.pop_screen()


class NewIssueModal(ModalScreen):
    BINDINGS = [("ESC, q", "cancel", "Cancel")]
    DEFAULT_CSS = """
    NewIssueModal {
        align: center middle;
    }

    NewIssueContainer {
        align: center middle;
        height: 30;
        width: 100;
        border: thick $background 80%;
        background: $surface-lighten-3;
    }
    """

    def __init__(self, repo: Repository, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.repo = repo

    def compose(self) -> ComposeResult:
        yield NewIssueContainer(self.repo)

    def action_cancel(self) -> None:
        self.dismiss()
