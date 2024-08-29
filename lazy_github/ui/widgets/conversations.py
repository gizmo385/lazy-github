from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Collapsible, Label, Markdown

from lazy_github.lib.github.client import GithubClient
from lazy_github.lib.github.pull_requests import ReviewCommentNode
from lazy_github.models.github import FullPullRequest, Review, ReviewComment, ReviewState
from lazy_github.ui.screens.new_comment import NewCommentModal


class ReviewCommentContainer(Container, can_focus=True):
    DEFAULT_CSS = """
    ReviewCommentContainer {
        height: auto;
        border-left: solid $secondary-background;
        margin-left: 1;
        margin-bottom: 1;
    }

    .comment-author {
        color: $text-muted;
        margin-left: 1;
        margin-bottom: 1;
    }

    Markdown {
        margin-left: 1;
        margin-bottom: 0;
        padding-bottom: 0;
    }

    ReviewCommentContainer:focus-within {
        border: dashed $success;
    }
    """

    BINDINGS = [("r", "reply_to_individual_comment", "Reply to comment")]

    def __init__(self, client: GithubClient, pr: FullPullRequest, comment: ReviewComment) -> None:
        super().__init__()
        self.client = client
        self.pr = pr
        self.comment = comment

    def compose(self) -> ComposeResult:
        comment_time = self.comment.created_at.strftime("%c")
        author = self.comment.user.login if self.comment.user else "Unknown"
        yield Markdown(self.comment.body)
        yield Label(f"{author} • {comment_time}", classes="comment-author")

    def action_reply_to_individual_comment(self) -> None:
        self.app.push_screen(NewCommentModal(self.client, self.pr.repo, self.pr, self.comment))


class ReviewConversation(Container):
    DEFAULT_CSS = """
    ReviewConversation {
        height: auto;
        border-left: solid $secondary-background;
        margin-bottom: 1;
    }
    """

    def __init__(self, client: GithubClient, pr: FullPullRequest, root_conversation_node: ReviewCommentNode) -> None:
        super().__init__()
        self.client = client
        self.pr = pr
        self.root_conversation_node = root_conversation_node

    def _flatten_comments(self, root: ReviewCommentNode) -> list[ReviewComment]:
        result = [root.comment]
        for child in root.children:
            result.extend(self._flatten_comments(child))
        return result

    def compose(self) -> ComposeResult:
        for comment in self._flatten_comments(self.root_conversation_node):
            yield ReviewCommentContainer(self.client, self.pr, comment)


class ReviewContainer(Collapsible, can_focus=True):
    DEFAULT_CSS = """
    ReviewContainer {
        height: auto;
    }

    ReviewContainer:focus-within {
        border: solid $success-lighten-3;
    }
    """
    BINDINGS = [("r", "reply_to_review", "Reply to review")]

    def __init__(
        self, client: GithubClient, pr: FullPullRequest, review: Review, hierarchy: dict[int, ReviewCommentNode]
    ) -> None:
        super().__init__()
        self.client = client
        self.pr = pr
        self.review = review
        self.hierarchy = hierarchy

    def compose(self) -> ComposeResult:
        if self.review.state == ReviewState.APPROVED:
            review_state_text = "[green]Approved[/green]"
        elif self.review.state == ReviewState.CHANGES_REQUESTED:
            review_state_text = "[red]Changes Requested[/red]"
        else:
            review_state_text = self.review.state.title()
        yield Label(f"Review from {self.review.user.login} ({review_state_text})")
        yield Markdown(self.review.body)
        for comment in self.review.comments:
            if comment_node := self.hierarchy[comment.id]:
                yield ReviewConversation(self.client, self.pr, comment_node)

    def action_reply_to_review(self) -> None:
        self.app.push_screen(NewCommentModal(self.client, self.pr.repo, self.pr, self.review))
