from typing import Self

from lazy_github.lib.github_v2.client import GithubClient


class PullRequest:
    def __init__(self, client: GithubClient, raw_data) -> None:
        self.client = client
        self._raw_data = raw_data

    @classmethod
    async def list_for_repo(cls, client: GithubClient, repo: str) -> list[Self]:
        return [cls(client, {})]
