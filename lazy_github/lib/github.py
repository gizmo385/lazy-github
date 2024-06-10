import httpx
import time
from typing import Optional
from dataclasses import dataclass
from textual import log


# https://docs.github.com/en/apps/creating-github-apps/writing-code-for-a-github-app/building-a-cli-with-a-github-app
_LAZY_GITHUB_CLIENT_ID = "Iv23limdG8Bl3Cu5FOcT"
_DEVICE_CODE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"


@dataclass
class DeviceCodeResponse:
    device_code: str
    verification_uri: str
    user_code: str
    polling_interval: int
    expires_at: int


@dataclass
class AccessTokenResponse:
    access_token: Optional[str]
    scope: Optional[str]
    token_type: Optional[str]
    error: Optional[str]


def get_device_code() -> DeviceCodeResponse:
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
    access_token_res = httpx.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": _LAZY_GITHUB_CLIENT_ID,
            "grant_type": _DEVICE_CODE_GRANT_TYPE,
            "device_code": device_code.device_code,
        },
    ).raise_for_status()
    access_token_data = dict(pair.split("=") for pair in access_token_res.text.split("&"))
    return AccessTokenResponse(
        access_token_data.get("access_token"),
        access_token_data.get("scope"),
        access_token_data.get("token_type"),
        access_token_data.get("error"),
    )


def _authenticate_on_terminal():
    # First we'll get the device code
    device_code = get_device_code()
    print(f"Please verify at: {device_code.verification_uri}")
    print(f"Your verification code is {device_code.user_code}")

    # Now we'll poll for an access token
    while True:
        access_token = get_access_token(device_code)
        match access_token.error:
            case "authorization_pending":
                log("Continuing to wait for auth...")
                time.sleep(device_code.polling_interval)
            case "slow_down":
                log("Continuing to wait for auth (slower)...")
                time.sleep(device_code.polling_interval + 5)
            case "expired_token":
                log("Your device code is expired :(")
            case "access_denied":
                log("Access denied :(")
            case _:
                log("Successfully authenticated!")
                break


if __name__ == "__main__":
    _authenticate_on_terminal()
