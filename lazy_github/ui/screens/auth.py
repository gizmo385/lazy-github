from functools import partial

from textual import log, work
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widget import Widget

import lazy_github.lib.github.auth as auth
from lazy_github.ui.screens.primary import LazyGithubMainScreen
from lazy_github.ui.widgets.common import LazyGithubFooter


class UserTokenDisplay(Widget):
    user_code: reactive[str | None] = reactive(None)

    def render(self):
        if self.user_code:
            return "\n".join(
                [
                    "Please verify at: https://github.com/login/device\n",
                    f"Your verification code is {self.user_code}",
                ]
            )
        else:
            return "Loading your device code..."


class AuthenticationModal(ModalScreen):
    DEFAULT_CSS = """
    AuthenticationModal {
        border: ascii red;
        align: center middle;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "GitHub Authentication"
        with Container():
            yield UserTokenDisplay()
            yield LazyGithubFooter()

    @work
    async def check_access_token(self, device_code: auth.DeviceCodeResponse):
        access_token = await auth.get_access_token(device_code)
        match access_token.error:
            case "authorization_pending":
                log("Continuing to wait for auth...")
            case "slow_down":
                log("Continuing to wait for auth (slower)...")
                self.access_token_timer.stop()
                log(self.access_token_timer)
                self.access_token_timer = self.set_interval(
                    device_code.polling_interval + 5,
                    partial(self.check_access_token, device_code),
                )
                log(self.access_token_timer)
            case "expired_token":
                log("your device code is expired :(")
                self.access_token_timer.stop()
            case "access_denied":
                log("Access denied :(")
                self.access_token_timer.stop()
            case _:
                log("Successfully authenticated!")
                auth.save_access_token(access_token)
                self.access_token_timer.stop()
                self.app.switch_screen(LazyGithubMainScreen())

    @work
    async def get_device_token(self):
        log("Attempting to get device code...")
        device_code = await auth.get_device_code()
        log(f"Device code: {device_code}")
        self.query_one(UserTokenDisplay).user_code = device_code.user_code

        # We want to check that the user has added the
        self.access_token_timer = self.set_interval(
            device_code.polling_interval, partial(self.check_access_token, device_code)
        )

    async def on_mount(self):
        # Once this screen starts, we need to start the auth flow. This begins by
        # requesting a device token from github and asking the user to input it on
        # the auth page.
        self.get_device_token()
