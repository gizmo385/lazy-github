from typing import Literal

from lazy_github.lib.github_v2.client import GithubClient
from lazy_github.models.core import Issue, PullRequest, Repository, User

IssueStateFilter = Literal["open"] | Literal["closed"] | Literal["all"]


async def _list(client: GithubClient, repo: Repository, state: IssueStateFilter) -> list[Issue]:
    query_params = {"state": state}
    user = await client.user
    response = await client.get(
        f"/repos/{user.login}/{repo.name}/issues", headers=client.headers_with_auth_accept(), params=query_params
    )
    result: list[Issue] = []
    for issue in response.json():
        if "draft" in issue:
            result.append(PullRequest(**issue))
        else:
            result.append(Issue(**issue))
    return result


if __name__ == "__main__":
    import asyncio

    from lazy_github.lib.config import Config
    from lazy_github.lib.github_v2.auth import token

    client = GithubClient(Config.load_config(), token())
    repo = Repository(
        name="discord.clj",
        full_name="gizmo385/discord.clj",
        default_branch="main",
        private=False,
        archived=False,
        owner=User(login="gizmo385", id=1),
    )
    issues = asyncio.run(_list(client, repo, "all"))
    for issue in issues:
        if isinstance(issue, PullRequest):
            print(f"Pull Request #{issue.number}: '{issue.title}' by {issue.user.login}")
        else:
            print(f"Issue #{issue.number}: {issue.title}")
