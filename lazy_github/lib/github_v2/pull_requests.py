from lazy_github.lib.github_v2.client import GithubClient
from lazy_github.lib.github_v2.issues import list_all_issues
from lazy_github.models.core import PullRequest, Repository


async def list_for_repo(client: GithubClient, repo: Repository) -> list[PullRequest]:
    issues = await list_all_issues(client, repo)
    return [i for i in issues if isinstance(i, PullRequest)]
