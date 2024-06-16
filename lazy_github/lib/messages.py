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
