from lazy_github.lib.constants import DIFF_CONTENT_ACCEPT_TYPE
from lazy_github.lib.context import LazyGithubContext, github_headers
from lazy_github.models.github import Branch, Repository


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
    url = f"/repos/{repo.owner.login}/{repo.name}/branches/{branch_name}"
    response = await LazyGithubContext.client.get(url, headers=github_headers())
    return Branch(**response.json())


async def compare_branches(repo: Repository, base_branch: Branch, head_branch: Branch) -> str:
    url = f"/repos/{repo.owner.login}/{repo.name}/compare/{base_branch.name}..{head_branch.name}"
    response = await LazyGithubContext.client.get(url, headers=github_headers(accept=DIFF_CONTENT_ACCEPT_TYPE))
    response.raise_for_status()
    return response.text
