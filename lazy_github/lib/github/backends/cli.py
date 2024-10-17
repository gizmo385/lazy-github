import asyncio
import json
import re
from typing import Any
from lazy_github.lib.config import Config
from lazy_github.lib.constants import JSON_CONTENT_ACCEPT_TYPE
from lazy_github.lib.github.backends.protocol import GithubBackendProtocol, GithubResponse, GithubStatusException
from lazy_github.models.github import User

header_regex = re.compile(r"\<.([^:]+):(.+)")


class CliGithubResponse(GithubResponse):
    def __init__(self, stdout: str, stderr: str) -> None:
        self._parse_stdout(stdout)
        self.stderr = stderr

    def _parse_stdout(self, stdout: str) -> None:
        extracted_headers: dict[str, str] = {}
        response_text: list[str] = []
        for line in stdout.splitlines():
            if line.startswith("*"):
                # This is metadata about the request
                pass
            elif line.startswith(">"):
                # This is the request
                pass
            elif line.startswith("<"):
                if matches := header_regex.match(line):
                    header_name = matches.group(1)
                    header_value = matches.group(2)
                    extracted_headers[header_name] = header_value
            else:
                # This is the raw response
                response_text.append(line)

        self._headers = extracted_headers
        self._raw_response = "\n".join(response_text)

    @property
    def headers(self) -> dict[str, str]:
        return self._headers

    def json(self) -> Any:
        return json.loads(self._raw_response)

    @property
    def text(self) -> str:
        return self._raw_response

    def raise_for_status(self) -> None:
        try:
            body = self.json()
        except json.JSONDecodeError:
            body = None

        if self.stderr:
            if body and "status" in body:
                raise GithubStatusException(body["status"], RuntimeError(self.stderr))
            else:
                raise GithubStatusException(-1, RuntimeError(self.stderr))


async def _run_gh_cli_api_command(
    url: str,
    method: str,
    accept_header: str = JSON_CONTENT_ACCEPT_TYPE,
    json_body: dict[str, str] | None = None,
) -> GithubResponse:
    command = f'gh api {url} -X {method} -H "Accept: {accept_header}"'
    if json_body:
        command += " ".join(f'-f "{k}={v}"' for k, v in json_body.items())

    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return CliGithubResponse(stdout.decode(), stderr.decode())


class GithubCliClient(GithubBackendProtocol):
    def __init__(self, config: Config):
        self.config = config

    async def user(self) -> User:
        result = await self.get("/user")
        result.raise_for_status()
        return User(**result.json())

    async def get(
        self,
        url: str,
        follow_redirects: bool = True,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> GithubResponse:
        _ = follow_redirects
        _ = params
        accept_header = headers.get("Accept", JSON_CONTENT_ACCEPT_TYPE) if headers else JSON_CONTENT_ACCEPT_TYPE
        return await _run_gh_cli_api_command(url, "GET", accept_header=accept_header)

    async def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, str] | None = None,
    ) -> GithubResponse:
        accept_header = headers.get("Accept", JSON_CONTENT_ACCEPT_TYPE) if headers else JSON_CONTENT_ACCEPT_TYPE
        return await _run_gh_cli_api_command(url, "POST", accept_header=accept_header, json_body=json)

    async def patch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, str] | None = None,
    ) -> GithubResponse:
        accept_header = headers.get("Accept", JSON_CONTENT_ACCEPT_TYPE) if headers else JSON_CONTENT_ACCEPT_TYPE
        return await _run_gh_cli_api_command(url, "PATCH", accept_header=accept_header, json_body=json)
