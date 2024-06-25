from lazy_github.lib.github.client import GithubClient
from lazy_github.lib.github.constants import DIFF_CONTENT_ACCEPT_TYPE
from lazy_github.lib.github.issues import list_all_issues
from lazy_github.models.github import FullPullRequest, PartialPullRequest, Repository


async def list_for_repo(client: GithubClient, repo: Repository) -> list[PartialPullRequest]:
    issues = await list_all_issues(client, repo)
    return [i for i in issues if isinstance(i, PartialPullRequest)]


async def get_full_pull_request(client: GithubClient, partial_pr: PartialPullRequest) -> FullPullRequest:
    """Converts a partial pull request into a full pull request"""
    user = await client.user()
    url = f"/repos/{user.login}/{partial_pr.repo.name}/pulls/{partial_pr.number}"
    response = await client.get(url, headers=client.headers_with_auth_accept())
    response.raise_for_status()
    return FullPullRequest(**response.json(), repo=partial_pr.repo)


async def get_diff(client: GithubClient, pr: FullPullRequest) -> str:
    """Fetches the raw diff for an individual pull request"""
    headers = client.headers_with_auth_accept(DIFF_CONTENT_ACCEPT_TYPE)
    response = await client.get(pr.diff_url, headers=headers, follow_redirects=True)
    response.raise_for_status()
    return response.text
