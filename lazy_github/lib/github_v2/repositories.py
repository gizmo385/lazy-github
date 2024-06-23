from functools import partial
from typing import Literal

from lazy_github.lib.github_v2.client import GithubClient
from lazy_github.models.core import Repository

RepoTypeFilter = Literal["all"] | Literal["owner"] | Literal["member"]
SortDirection = Literal["asc"] | Literal["desc"]
RepositorySortKey = Literal["created"] | Literal["updated"] | Literal["pushed"] | Literal["full_name"]


async def _list(
    client: GithubClient,
    repo_types: RepoTypeFilter,
    sort: RepositorySortKey = "full_name",
    direction: SortDirection = "asc",
    page: int = 1,
    per_page: int = 30,
) -> list[Repository]:
    """Retrieves Github repos matching the specified criteria"""
    query_params = {"type": repo_types, "direction": direction, "sort": sort, "page": page, "per_page": per_page}
    user = await client.user
    response = await client.get(
        f"/users/{user.login}/repos", headers=client.headers_with_auth_accept(), params=query_params
    )
    return [Repository(**r) for r in response.json()]


list_all = partial(_list, repo_types="all")
list_owned = partial(_list, repo_types="owner")
list_member_of = partial(_list, repo_types="member")
