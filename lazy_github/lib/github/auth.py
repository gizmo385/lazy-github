import time
from dataclasses import dataclass
from typing import Optional

import httpx

from lazy_github.lib.constants import CONFIG_FOLDER, DEVICE_CODE_GRANT_TYPE, LAZY_GITHUB_CLIENT_ID
from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.github.backends.protocol import BackendType

# Auth and client globals
_AUTHENTICATION_CACHE_LOCATION = CONFIG_FOLDER / "auth.text"
_AUTH_TOKEN: Optional[str] = None


@dataclass
class DeviceCodeResponse:
    device_code: str
    verification_uri: str
    user_code: str
    polling_interval: int
    expires_at: int


@dataclass
class AccessTokenResponse:
    token: Optional[str]
    error: Optional[str]


class GithubAuthenticationRequired(Exception):
    pass


async def get_device_code() -> DeviceCodeResponse:
    """
    Authenticates this device with the Github API. This will require the user to go enter the provided device code on
    the Github UI to authenticate the LazyGithub app.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/device/code",
            data={"client_id": LAZY_GITHUB_CLIENT_ID},
            headers={"Accept": "application/json"},
        )

    response.raise_for_status()
    body = response.json()
    expires_at = time.time() + body["expires_in"]
    return DeviceCodeResponse(
        body["device_code"],
        body["verification_uri"],
        body["user_code"],
        body["interval"],
        expires_at,
    )


async def get_access_token(device_code: DeviceCodeResponse) -> AccessTokenResponse:
    """Given a device code, retrieves the oauth access token that can be used to send requests to the GIthub API"""
    async with httpx.AsyncClient() as client:
        # TODO: This should specify an accept
        access_token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": LAZY_GITHUB_CLIENT_ID,
                "grant_type": DEVICE_CODE_GRANT_TYPE,
                "device_code": device_code.device_code,
            },
        )
    access_token_res.raise_for_status()
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


def get_api_token() -> str:
    """
    Helper function which loads the token from the file on disk. If the file does not exist, it raises a
    GithubAuthenticationRequired exception that the caller should handle by triggering the auth flow
    """
    global _AUTH_TOKEN
    if _AUTH_TOKEN is not None:
        return _AUTH_TOKEN

    if not _AUTHENTICATION_CACHE_LOCATION.exists():
        raise GithubAuthenticationRequired()
    _AUTH_TOKEN = _AUTHENTICATION_CACHE_LOCATION.read_text().strip()
    return _AUTH_TOKEN


async def is_logged_in_to_cli() -> bool:
    """Checks to see if the user is currently logged into the GitHub CLI"""
    # Avoiding circular imports
    from lazy_github.lib.github.backends.cli import run_gh_cli_command
    from lazy_github.lib.logging import lg

    try:
        result = await run_gh_cli_command(["auth", "status"])
        return result.return_code == 0
    except Exception:
        lg.exception("Error checking if github CLI is authenticated")
        return False


async def assert_is_logged_in() -> None:
    """
    Abstraction over the login checks we perform for the different backend implementations. Returns True if the user is
    logged in and can send requests via their selected backend
    """
    match LazyGithubContext.client_type:
        case BackendType.RAW_HTTP:
            get_api_token()
        case BackendType.GITHUB_CLI:
            if not await is_logged_in_to_cli():
                raise GithubAuthenticationRequired()
