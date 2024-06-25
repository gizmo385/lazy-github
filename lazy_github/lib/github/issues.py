from functools import partial
from typing import Literal

from lazy_github.lib.github.client import GithubClient
from lazy_github.models.github import Issue, PartialPullRequest, Repository, User

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


if __name__ == "__main__":
    import asyncio
    import logging

    logging.basicConfig(
        format="%(levelname)s [%(asctime)s] %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG
    )

    from lazy_github.lib.config import Config
    from lazy_github.lib.github.auth import token

    client = GithubClient(Config.load_config(), token())
    repo = Repository(
        name="discord.clj",
        full_name="gizmo385/discord.clj",
        default_branch="main",
        private=False,
        archived=False,
        owner=User(login="gizmo385", id=1, html_url="wat"),
    )
    issues = asyncio.run(_list(client, repo, "all"))
    for issue in issues:
        if isinstance(issue, PartialPullRequest):
            print(f"Pull Request #{issue.number}: '{issue.title}' by {issue.user.login}")
        else:
            print(f"Issue #{issue.number}: {issue.title}")
