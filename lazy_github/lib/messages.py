from github.PullRequest import PullRequest
from github.Repository import Repository
from textual.message import Message


class RepoSelected(Message):
    """
    A message indicating that a particular user repo has been selected.

    This message is used to trigger follow-up contextual actions based on the selected repo, such as loading pull
    requests, issues, actions, etc.
    """

    def __init__(self, repo: Repository) -> None:
        self.repo = repo
        super().__init__()


class PullRequestSelected(Message):
    """
    A message indicating that the user is looking for additional information on a particular pull request.
    """

    def __init__(self, pr: PullRequest) -> None:
        self.pr = pr
        super().__init__()
