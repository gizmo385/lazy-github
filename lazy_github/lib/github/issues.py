from lazy_github.lib.github.client import GithubClient
from lazy_github.models.github import Issue, IssueComment, PartialPullRequest, Repository
from lazy_github.lib.constants import IssueStateFilter, IssueOwnerFilter


async def list_issues(
    client: GithubClient, repo: Repository, state: IssueStateFilter, owner: IssueOwnerFilter
) -> list[Issue]:
    """Fetch issues (included pull requests) from the repo matching the state/owner filters"""
    query_params = {"state": str(state).lower()}
    if owner == IssueOwnerFilter.MINE:
        user = await client.user()
        query_params["creator"] = user.login

    headers = client.headers_with_auth_accept(cache_duration=client.config.cache.list_issues_ttl)
    response = await client.get(f"/repos/{repo.owner.login}/{repo.name}/issues", headers=headers, params=query_params)
    response.raise_for_status()
    result: list[Issue] = []
    for issue in response.json():
        if "draft" in issue:
            result.append(PartialPullRequest(**issue, repo=repo))
        else:
            result.append(Issue(**issue, repo=repo))
    return result


async def get_comments(client: GithubClient, issue: Issue) -> list[IssueComment]:
    response = await client.get(issue.comments_url, headers=client.headers_with_auth_accept())
    response.raise_for_status()
    return [IssueComment(**i) for i in response.json()]


async def create_comment(client: GithubClient, repo: Repository, issue: Issue, comment_body: str) -> IssueComment:
    url = f"/repos/{repo.owner.login}/{repo.name}/issues/{issue.number}/comments"
    body = {"body": comment_body}
    response = await client.post(url, json=body, headers=client.headers_with_auth_accept())
    response.raise_for_status()
    return IssueComment(**response.json())
