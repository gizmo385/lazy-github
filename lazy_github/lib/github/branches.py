from lazy_github.models.github import Branch, Repository
from lazy_github.lib.context import LazyGithubContext, github_headers


async def list_branches(repo: Repository, per_page: int = 30, page: int = 1) -> list[Branch]:
    """List branches on the specified repo"""
    query_params = {"page": page, "per_page": per_page}
    response = await LazyGithubContext.client.get(
        f"/repos/{repo.owner.login}/{repo.name}/branches",
        headers=github_headers(),
        params=query_params,
    )
    response.raise_for_status()
    return [Branch(**branch) for branch in response.json()]


async def get_branch(repo: Repository, branch_name: str) -> Branch | None:
    url = (f"/repos/{repo.owner.login}/{repo.name}/branches/{branch_name}",)
    response = await LazyGithubContext.client.get(url, headers=github_headers())
    return Branch(**response.json())