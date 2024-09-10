from typing import TypedDict, Unpack

import lazy_github.lib.github.client as github
from lazy_github.lib.config import Config
from lazy_github.lib.constants import IssueOwnerFilter, IssueStateFilter
from lazy_github.models.github import Issue, IssueComment, PartialPullRequest, Repository


class UpdateIssuePayload(TypedDict):
    title: str | None
    body: str | None
    state: str | None


async def list_issues(repo: Repository, state: IssueStateFilter, owner: IssueOwnerFilter) -> list[Issue]:
    """Fetch issues (included pull requests) from the repo matching the state/owner filters"""
    query_params = {"state": str(state).lower()}
    if owner == IssueOwnerFilter.MINE:
        user = await github.user()
        query_params["creator"] = user.login

    config = Config.load_config()
    headers = github.headers_with_auth_accept(cache_duration=config.cache.list_issues_ttl)
    response = await github.get(f"/repos/{repo.owner.login}/{repo.name}/issues", headers=headers, params=query_params)
    response.raise_for_status()
    result: list[Issue] = []
    for issue in response.json():
        if "draft" in issue:
            result.append(PartialPullRequest(**issue, repo=repo))
        else:
            result.append(Issue(**issue, repo=repo))
    return result


async def get_comments(issue: Issue) -> list[IssueComment]:
    response = await github.get(issue.comments_url, headers=github.headers_with_auth_accept())
    response.raise_for_status()
    return [IssueComment(**i) for i in response.json()]


async def create_comment(issue: Issue, comment_body: str) -> IssueComment:
    url = f"/repos/{issue.repo.owner.login}/{issue.repo.name}/issues/{issue.number}/comments"
    body = {"body": comment_body}
    response = await github.post(url, json=body, headers=github.headers_with_auth_accept())
    response.raise_for_status()
    return IssueComment(**response.json())


async def update_issue(issue_to_update: Issue, **updated_fields: Unpack[UpdateIssuePayload]) -> Issue:
    repo = issue_to_update.repo
    url = f"/repos/{repo.owner.login}/{repo.name}/issues/{issue_to_update.number}"
    response = await github.patch(url, json=updated_fields, headers=github.headers_with_auth_accept())
    response.raise_for_status()
    return Issue(**response.json(), repo=repo)


async def create_issue(repo: Repository, title: str, body: str) -> Issue:
    url = f"/repos/{repo.owner.login}/{repo.name}/issues"
    json_body = {"title": title, "body": body}
    response = await github.post(url, json=json_body, headers=github.headers_with_auth_accept())
    response.raise_for_status()
    return Issue(**response.json(), repo=repo)
