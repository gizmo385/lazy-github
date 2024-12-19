from lazy_github.lib.context import LazyGithubContext, github_headers
from lazy_github.models.github import CombinedCheckStatus, Repository


async def combined_check_status_for_ref(
    repo: Repository, ref: str, per_page: int = 100, page: int = 1
) -> CombinedCheckStatus:
    query_params = {"page": page, "per_page": per_page}
    response = await LazyGithubContext.client.get(
        f"/repos/{repo.owner.login}/{repo.name}/commits/{ref}/status", headers=github_headers(), params=query_params
    )
    response.raise_for_status()
    return CombinedCheckStatus(**response.json())
