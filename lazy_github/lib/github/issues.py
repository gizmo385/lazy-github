from functools import partial
from typing import Literal

from lazy_github.lib.github.client import GithubClient
from lazy_github.models.github import Issue, PartialPullRequest, Repository

IssueStateFilter = Literal["open"] | Literal["closed"] | Literal["all"]


async def _list(client: GithubClient, repo: Repository, state: IssueStateFilter) -> list[Issue]:
    query_params = {"state": state}
    user = await client.user()
    response = await client.get(
        f"/repos/{user.login}/{repo.name}/issues", headers=client.headers_with_auth_accept(), params=query_params
    )
    result: list[Issue] = []
    for issue in response.json():
        if "draft" in issue:
            result.append(PartialPullRequest(**issue, repo=repo))
        else:
            result.append(Issue(**issue, repo=repo))
    return result


list_open_issues = partial(_list, state="open")
list_closed_issues = partial(_list, state="closed")
list_all_issues = partial(_list, state="all")


async def get_comments(client: GithubClient, issue: Issue) -> list:
    response = await client.get(issue.comments_url, headers=client.headers_with_auth_accept())
    response.raise_for_status()
    return response.json()
