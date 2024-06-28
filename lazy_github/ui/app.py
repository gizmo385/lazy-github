from textual import log
from textual.app import App

from lazy_github.lib.config import Config
from lazy_github.lib.github.auth import GithubAuthenticationRequired, token
from lazy_github.lib.github.client import GithubClient
from lazy_github.ui.screens.auth import AuthenticationModal
from lazy_github.ui.screens.primary import LazyGithubMainScreen


class LazyGithub(App):
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("q", "quit", "Quit"), ("ctrl+p", "command_palette")]

    async def authenticate_with_github(self):
        config = Config.load_config()
        try:
            access_token = token()
            client = GithubClient(config, access_token)
            self.push_screen(LazyGithubMainScreen(client))
        except GithubAuthenticationRequired:
            log("Triggering auth with github")
            self.push_screen(AuthenticationModal(id="auth-modal"))

    async def on_ready(self):
        await self.authenticate_with_github()


app = LazyGithub()
