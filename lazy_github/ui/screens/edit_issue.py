from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Rule, TextArea

from lazy_github.lib.github import issues
from lazy_github.models.github import Issue


class EditIssueContainer(Container):
    DEFAULT_CSS = """
    #button_holder {
        align: center middle;
    }

    #updated_issue_body {
        height: 15;
    }
    """

    def __init__(self, issue: Issue, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.issue = issue

    def compose(self) -> ComposeResult:
        yield Label("[bold]Title[/bold]")
        yield Input(self.issue.title, id="updated_issue_title")

        yield Rule()

        yield Label("[bold]Description[/bold]")
        yield TextArea.code_editor(self.issue.body or "", id="updated_issue_body", soft_wrap=True)

        with Horizontal(id="button_holder"):
            yield Button("Save", id="save_updated_issue", variant="success")
            yield Button("Cancel", id="cancel_updated_issue", variant="error")

    @on(Button.Pressed, "#cancel_updated_issue")
    def cancel_updated_issue(self, _: Button) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#save_updated_issue")
    async def submit_updated_issue(self, save_button: Button) -> None:
        save_button.label = "Saving..."
        save_button.disabled = True
        updated_title = self.query_one("#updated_issue_title", Input).value
        updated_body = self.query_one("#updated_issue_body", TextArea).text
        self.notify(f"Updating issue #{self.issue.number}...", timeout=1)
        await issues.update_issue(self.issue, title=updated_title, body=updated_body)
        self.notify(f"Successfully updated issue #{self.issue.number}")
        self.app.pop_screen()


class EditIssueModal(ModalScreen):
    DEFAULT_CSS = """
    EditIssueModal {
        align: center middle;
    }

    EditIssueContainer {
        align: center middle;
        height: 30;
        width: 100;
        border: thick $background 80%;
        background: $surface;
    }
    """

    def __init__(self, issue: Issue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.issue = issue

    def compose(self) -> ComposeResult:
        yield EditIssueContainer(self.issue)
