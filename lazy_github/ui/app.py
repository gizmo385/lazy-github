from textual import log
from textual.app import App

import lazy_github.lib.github as g
from lazy_github.lib.config import Config
from lazy_github.lib.github_v2.auth import token
from lazy_github.lib.github_v2.client import GithubClient
from lazy_github.ui.screens.auth import AuthenticationModal
from lazy_github.ui.screens.primary import LazyGithubMainScreen


class LazyGithub(App):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    async def authenticate_with_github(self):
        config = Config.load_config()
        try:
            access_token = token()
            client = GithubClient(config, access_token)
            self.push_screen(LazyGithubMainScreen(client))
        except g.GithubAuthenticationRequired:
            log("Triggering auth with github")
            self.push_screen(AuthenticationModal(id="auth-modal"))

    async def on_ready(self):
        await self.authenticate_with_github()


app = LazyGithub()
