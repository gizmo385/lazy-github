import json
from pathlib import Path
import re
import tempfile
import asyncio
from typing import Any

from lazy_github.lib.config import Config
from lazy_github.lib.constants import CONFIG_FOLDER, JSON_CONTENT_ACCEPT_TYPE
from lazy_github.lib.github.backends.protocol import GithubApiBackend, GithubApiRequestFailed, GithubApiResponse
from lazy_github.models.github import User


_HEADER_RE = re.compile(r"^([a-zA-Z-]+)\:(.+)$")
TEMPORARY_JSON_BODY_DIRECTORY = CONFIG_FOLDER / "request_bodies"


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


def _clear_temporary_bodies() -> None:
    for filepath in TEMPORARY_JSON_BODY_DIRECTORY.glob("*"):
        Path(filepath).unlink(missing_ok=True)


async def run_gh_cli_command(command: list[str]) -> CliApiResponse:
    """Simple wrapper around running a Github CLI command"""
    from lazy_github.lib.logging import lg

    proc = await asyncio.create_subprocess_exec(
        "gh", *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    lg.debug(f"Running Github CLI command: gh {' '.join(command)}")

    try:
        raw_stdout, raw_stderr = await proc.communicate()
        stderr = raw_stderr.decode()
        if raw_stderr:
            lg.debug(f"Error output from Github CLI: {stderr}")
    except Exception:
        lg.exception("Couldn't communicate with gh cli proc")
        # TODO: Is this actually how we want to handle an exception case here?
        response = _parse_cli_api_response(255, "", "")
    else:
        return_code = proc.returncode if proc.returncode is not None else 255
        response = _parse_cli_api_response(return_code, raw_stdout.decode(), stderr)

    _clear_temporary_bodies()

    return response


def _build_command(
    base_url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    query_params: dict[str, str] | None = None,
    body: dict[str, str] | None = None,
) -> list[str]:
    command = ["api", "-i", "-X", method]

    if headers:
        for header_name, header_value in headers.items():
            command.extend(["-H", f"{header_name}: {header_value}"])

    if query_params:
        for param_name, param_value in query_params.items():
            command.extend(["-F", f"{param_name}={param_value}"])

    if body:
        TEMPORARY_JSON_BODY_DIRECTORY.mkdir(parents=True, exist_ok=True)
        temp = tempfile.NamedTemporaryFile(delete=False, delete_on_close=False, dir=TEMPORARY_JSON_BODY_DIRECTORY)
        temp.write(json.dumps(body).encode())
        command.extend(["--input", str(temp.name)])

    command.append(base_url)

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
        json: dict[str, str] | None = None,
    ) -> Any:
        command = _build_command(url, headers=headers, body=json, method="POST")
        return await run_gh_cli_command(command)

    async def patch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, str] | None = None,
    ) -> Any:
        command = _build_command(url, headers=headers, body=json, method="PATCH")
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
    query_params = {"type": "all", "direction": "asc", "sort": "full_name", "page": 1, "per_page": 20}
    breakpoint()
    response = await client.get("/user/repos", params=query_params)
    print(response)
    print(response.return_code)
    print(response.json())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())