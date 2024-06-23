import time
from dataclasses import dataclass

import httpx
from github import Auth, Github
from github.PullRequest import PullRequest

from lazy_github.lib.constants import CONFIG_FOLDER

# Github constants
_DIFF_CONTENT_ACCEPT_TYPE = "application/vnd.github.diff"
_JSON_CONTENT_ACCEPT_TYPE = "application/vnd.github+json"
_LAZY_GITHUB_CLIENT_ID = "Iv23limdG8Bl3Cu5FOcT"
_DEVICE_CODE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"

# Auth and client globals
_AUTHENTICATION_CACHE_LOCATION = CONFIG_FOLDER / "auth.text"
_GITHUB_CLIENT: Github | None = None
_AUTH_TOKEN: str | None = None


class GithubAuthenticationRequired(Exception):
    pass


@dataclass
class DeviceCodeResponse:
    device_code: str
    verification_uri: str
    user_code: str
    polling_interval: int
    expires_at: int


@dataclass
class AccessTokenResponse:
    token: str | None
    error: str | None


def get_device_code() -> DeviceCodeResponse:
    """
    Authenticates this device with the Github API. This will require the user to go enter the provided device code on
    the Github UI to authenticate the LazyGithub app.
    """
    response = (
        httpx.post(
            "https://github.com/login/device/code",
            data={"client_id": _LAZY_GITHUB_CLIENT_ID},
            headers={"Accept": "application/json"},
        )
        .raise_for_status()
        .json()
    )
    expires_at = time.time() + response["expires_in"]
    return DeviceCodeResponse(
        response["device_code"],
        response["verification_uri"],
        response["user_code"],
        response["interval"],
        expires_at,
    )


def get_access_token(device_code: DeviceCodeResponse) -> AccessTokenResponse:
    """Given a device code, retrieves the oauth access token that can be used to send requests to the GIthub API"""
    access_token_res = httpx.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": _LAZY_GITHUB_CLIENT_ID,
            "grant_type": _DEVICE_CODE_GRANT_TYPE,
            "device_code": device_code.device_code,
        },
    ).raise_for_status()
    pairs = access_token_res.text.split("&")
    access_token_data = dict(pair.split("=") for pair in pairs)
    return AccessTokenResponse(
        access_token_data.get("access_token"),
        access_token_data.get("error"),
    )


def save_access_token(access_token: AccessTokenResponse) -> None:
    """Writes the returned access token to the config location"""
    if not access_token.token:
        raise ValueError("Invalid access token response! Cannot save")

    # Create the parent directories for our cache if it's present
    _AUTHENTICATION_CACHE_LOCATION.parent.mkdir(parents=True, exist_ok=True)
    _AUTHENTICATION_CACHE_LOCATION.write_text(access_token.token)


def github_client() -> Github:
    """Creates a PyGithub client with the saved auth token"""
    global _GITHUB_CLIENT
    if _GITHUB_CLIENT is not None:
        return _GITHUB_CLIENT

    if not _AUTHENTICATION_CACHE_LOCATION.exists():
        raise GithubAuthenticationRequired()
    token = _AUTHENTICATION_CACHE_LOCATION.read_text().strip()
    _GITHUB_CLIENT = Github(auth=Auth.Token(token))
    return _GITHUB_CLIENT


def token() -> str:
    global _AUTH_TOKEN
    if _AUTH_TOKEN is not None:
        return _AUTH_TOKEN

    if not _AUTHENTICATION_CACHE_LOCATION.exists():
        raise GithubAuthenticationRequired()
    _AUTH_TOKEN = _AUTHENTICATION_CACHE_LOCATION.read_text().strip()
    return _AUTH_TOKEN


def get(url: str, accept: str = _JSON_CONTENT_ACCEPT_TYPE) -> httpx.Response:
    """Wrapper function around sending a GET request to Github with the appropriate token"""
    github_token = token()
    headers = {"Accept": accept, "Authorization": f"Bearer {github_token}"}
    return httpx.get(url, headers=headers).raise_for_status()


def get_diff(pr: PullRequest) -> str:
    """Given a PR object from github, retrieves the diff for that PR"""
    return get(pr.raw_data["url"], accept=_DIFF_CONTENT_ACCEPT_TYPE).raise_for_status().text


def get_conversation(pr: PullRequest) -> str:
    """Given a PR object from github, retrieves the diff for that PR"""
    return get(pr.raw_data["comments_url"]).raise_for_status().text


def get_reviews(pr: PullRequest) -> str:
    """Given a PR object from github, retrieves the diff for that PR"""
    return get(pr.raw_data["review_comments_url"]).raise_for_status().text


if __name__ == "__main__":
    client = github_client()

    # This PR: https://github.com/gizmo385/lazy-github/pull/1
    LAZY_GITHUB_REPO_ID = 812868589
    repo = client.get_repo(LAZY_GITHUB_REPO_ID)
    print(repo.raw_data)
    pr = repo.get_pulls()[0]
    print(get_diff(pr))
