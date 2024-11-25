from httpx import HTTPError

from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.logging import lg
from lazy_github.models.github import Repository, Workflow, WorkflowRun


async def list_workflows(repository: Repository, page: int = 1, per_page: int = 30) -> list[Workflow]:
    """Lists available Github action workflows on the specified repo"""
    query_params = {"page": page, "per_page": per_page}
    url = f"/repos/{repository.owner.login}/{repository.name}/actions/workflows"
    try:
        response = await LazyGithubContext.client.get(url, params=query_params)
        response.raise_for_status()
        raw_json = response.json()
    except HTTPError:
        lg.exception("Error retrieving actions from the Github API")
        return []
    else:
        if workflows := raw_json.get("workflows"):
            return [Workflow(**w) for w in workflows]
        else:
            return []


async def list_workflow_runs(repository: Repository, page: int = 1, per_page: int = 30) -> list[WorkflowRun]:
    """Lists github workflows runs on the specified repo"""
    query_params = {"page": page, "per_page": per_page}
    url = f"/repos/{repository.owner.login}/{repository.name}/actions/runs"

    try:
        response = await LazyGithubContext.client.get(url, params=query_params)
        response.raise_for_status()
        raw_json = response.json()
    except HTTPError:
        lg.exception("Error retrieving action runs from the Github API")
        return []
    else:
        if workflows := raw_json.get("workflow_runs"):
            return [WorkflowRun(**w) for w in workflows]
        else:
            return []
