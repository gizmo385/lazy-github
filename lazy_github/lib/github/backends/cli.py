import json

from lazy_github.lib.github.backends.protocol import GithubApiBackend
from lazy_github.lib.github_cli import run_gh_cli_command


class GithubCliBackend(GithubApiBackend):
    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
    ) -> dict[str, str]:
        result = await run_gh_cli_command(["api", url])
        return json.loads(result.stdout)

    async def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, str] | None = None,
    ) -> dict[str, str]:
        result = await run_gh_cli_command(["api", "--post", url])
        return json.loads(result.stdout)

    async def patch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, str] | None = None,
    ) -> dict[str, str]:
        result = await run_gh_cli_command(["api", "--patch", url])
        return json.loads(result.stdout)
