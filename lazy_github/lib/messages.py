from functools import cached_property

from textual.message import Message

from lazy_github.models.github import Issue, PartialPullRequest, Repository


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

    def __init__(self, pr: PartialPullRequest) -> None:
        self.pr = pr
        super().__init__()


class IssuesAndPullRequestsFetched(Message):
    """
    Since issues and pull requests are both represented on the Github API as issues, we want to pull issues once and
    then send that message to both sections of the UI.
    """

    def __init__(self, issues_and_pull_requests: list[Issue]) -> None:
        self.issues_and_pull_requests = issues_and_pull_requests
        super().__init__()

    @cached_property
    def pull_requests(self) -> list[PartialPullRequest]:
        return [pr for pr in self.issues_and_pull_requests if isinstance(pr, PartialPullRequest)]

    @cached_property
    def issues(self) -> list[Issue]:
        return [
            issue
            for issue in self.issues_and_pull_requests
            if isinstance(issue, Issue) and not isinstance(issue, PartialPullRequest)
        ]
