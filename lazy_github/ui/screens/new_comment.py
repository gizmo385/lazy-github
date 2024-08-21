from httpx import HTTPStatusError
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Markdown, Rule, TextArea

from lazy_github.lib.github import issues, pull_requests
from lazy_github.lib.github.client import GithubClient
from lazy_github.models.github import Issue, Repository, Review, ReviewComment
from lazy_github.ui.widgets.command_log import log_event

CommmentReplyTarget = ReviewComment | Review


class ReplyingToContainer(Container):
    def __init__(self, reply_to: CommmentReplyTarget, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.reply_to = reply_to

    def compose(self) -> ComposeResult:
        if isinstance(self.reply_to, ReviewComment):
            comment_time = self.reply_to.created_at.strftime("%c")
        else:
            comment_time = self.reply_to.submitted_at.strftime("%c")

        author = self.reply_to.user.login if self.reply_to.user else "Unknown"
        yield Label(f"Replying to comment from {author} at {comment_time}")
        yield Markdown(self.reply_to.body)
        yield Rule()


class NewCommentContainer(Container):
    DEFAULT_CSS = """
    #new_comment_body {
        border: blank white ;
        min-height: 40%;
        width: 100%;
        padding-top: 1;
    }

    #comment_preview {
        border: blank white;
        min-height: 40%;
        width: 100%;
        padding-top: 1;
    }

    Horizontal {
        align: center middle;
    }
    """

    def __init__(
        self,
        client: GithubClient,
        repo: Repository,
        issue: Issue,
        reply_to: CommmentReplyTarget | None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.reply_to = reply_to
        self.client = client
        self.repo = repo
        self.issue = issue

    def compose(self) -> ComposeResult:
        if self.reply_to:
            yield ReplyingToContainer(self.reply_to)
        yield Label("New comment")
        yield TextArea(id="new_comment_body")
        yield Label("Preview")
        yield Markdown(id="comment_preview")
        with Horizontal():
            yield Button("Post Comment", id="post_comment", variant="success")
            yield Button("Cancel", id="cancel_comment", variant="error")

    @on(TextArea.Changed, "#new_comment_body")
    async def comment_updated(self, updated_message: TextArea.Changed) -> None:
        self.query_one("#comment_preview", Markdown).update(updated_message.text_area.text)

    @on(Button.Pressed, "#post_comment")
    async def post_comment(self, _: Button.Pressed) -> None:
        body = self.query_one("#new_comment_body", TextArea).text
        try:
            if isinstance(self.reply_to, ReviewComment):
                await pull_requests.reply_to_review_comment(self.client, self.repo, self.issue, self.reply_to, body)
            else:
                await issues.create_comment(self.client, self.repo, self.issue, body)
        except HTTPStatusError as hse:
            # TODO: We should handle the error case better here
            log_event(f"Error while posting comment for issue #{self.issue.number}: {hse}")
            self.app.pop_screen()
        else:
            log_event(f"Successfully posted new comment for issue #{self.issue.number}")
            self.app.pop_screen()

    @on(Button.Pressed, "#cancel_comment")
    def cancel_comment(self, _: Button.Pressed) -> None:
        self.app.pop_screen()


class NewCommentModal(ModalScreen):
    DEFAULT_CSS = """
    NewCommentModal {
        border: ascii green;
        align: center middle;
        content-align: center middle;
    }

    NewCommentContainer {
        width: 100;
        height: 50;
        border: thick $background 80%;
        background: $surface;
        margin: 1;
    }
    """

    BINDINGS = [("ESC, q", "cancel", "Cancel")]

    def __init__(
        self,
        client: GithubClient,
        repo: Repository,
        issue: Issue,
        reply_to: CommmentReplyTarget | None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.reply_to = reply_to
        self.client = client
        self.repo = repo
        self.issue = issue

    def compose(self) -> ComposeResult:
        yield NewCommentContainer(self.client, self.repo, self.issue, self.reply_to)

    def action_cancel(self) -> None:
        self.app.pop_screen()
