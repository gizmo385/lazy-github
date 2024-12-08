import json
import re
import subprocess
import tempfile
from asyncio import sleep
from typing import Any
from urllib.parse import urlencode

from textual.dom import QueryOneCacheKey

from lazy_github.lib.config import Config
from lazy_github.lib.constants import JSON_CONTENT_ACCEPT_TYPE
from lazy_github.lib.github.backends.protocol import GithubApiBackend, GithubApiRequestFailed, GithubApiResponse
from lazy_github.models.github import User


_HEADER_RE = re.compile(r"^([a-zA-Z-]+)\:(.+)$")


class CliApiResponse(GithubApiResponse):
    def __init__(self, return_code: int, http_status: int, stdout: str, stderr: str, headers: dict[str, str]) -> None:
        self.return_code = return_code
        self.http_status = http_status
        self.stdout = stdout
        self.stderr = stderr
        self._headers = headers

    def is_success(self) -> bool:
        return self.return_code == 0 and self.http_status < 300

    def raise_for_status(self) -> None:
        if not self.is_success():
            raise GithubApiRequestFailed({"error": self.stderr, "http_status": self.http_status})

    def json(self) -> Any:
        return json.loads(self.stdout)

    @property
    def text(self) -> str:
        return self.stdout

    @property
    def headers(self) -> dict[str, str]:
        return self._headers


def _parse_cli_api_response(return_code: int, stdout: str, stderr: str) -> CliApiResponse:
    headers = {}
    http_status: int = 0
    response_content = []
    for line in stdout.splitlines():
        if not line:
            continue

        if line.lower().startswith("http/2.0"):
            http_status = int(line.split(" ")[1])
        elif header_components := _HEADER_RE.match(line):
            headers[header_components.group(1)] = header_components.group(2)
        else:
            response_content.append(line)
    return CliApiResponse(return_code, http_status, "\n".join(response_content), stderr, headers)


async def run_gh_cli_command(command: list[str]) -> CliApiResponse:
    """Simple wrapper around running a Github CLI command"""
    from lazy_github.lib.logging import lg

    full_command = ["gh"] + command
    lg.debug(" ".join(full_command))
    print(" ".join(full_command))
    proc = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        if proc.poll() is not None:
            raw_stdout, raw_stderr = proc.communicate()
            return _parse_cli_api_response(proc.returncode, raw_stdout.decode(), raw_stderr.decode())
        else:
            await sleep(0.5)


def _build_command(
    base_url: str,
    method: str | None = None,
    headers: dict[str, str] | None = None,
    query_params: dict[str, str] | None = None,
    body: dict[str, str] | None = None,
) -> list[str]:
    command = ["api", "-i"]
    if method:
        command.append(f"--{method.lower()}")

    if headers:
        for header_name, header_value in headers.items():
            command.extend(["-H", f'"{header_name}: {header_value}"'])

    if query_params:
        encoded_params = urlencode(tuple(query_params.items()))
        command.append(f'"{base_url}?{encoded_params}"')
    else:
        command.append(base_url)

    if body:
        temp = tempfile.TemporaryFile()
        temp.write(json.dumps(body).encode())
        command.extend(["--input", temp.name])

    return command


class GithubCliBackend(GithubApiBackend):
    def __init__(self, config: Config) -> None:
        self.config = config

    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        command = _build_command(url, headers=headers, query_params=params)
        return await run_gh_cli_command(command)

    async def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, str] | None = None,
    ) -> Any:
        command = _build_command(url, headers=headers, body=body, method="POST")
        return await run_gh_cli_command(command)

    async def patch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, str] | None = None,
    ) -> Any:
        command = _build_command(url, headers=headers, body=body, method="PATCH")
        return await run_gh_cli_command(command)

    async def get_user(self) -> User:
        response = await self.get("/user")
        return User(**response.json())

    def github_headers(
        self, accept: str = JSON_CONTENT_ACCEPT_TYPE, cache_duration: int | None = None
    ) -> dict[str, str]:
        """Helper function to build a request with specific headers"""
        max_age = cache_duration or self.config.cache.default_ttl
        return {"Accept": accept, "Cache-Control": f"max-age={max_age}"}


async def main():
    client = GithubCliBackend(Config.load_config())
    response = await client.get("/user/repos")
    # response = _parse_cli_api_response(0, test_response, "")
    print(response)
    print(response.return_code)
    print(response.json())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
