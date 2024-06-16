from textual import log
from textual.app import App

import lazy_github.lib.github as g
from lazy_github.ui.screens.auth import AuthenticationModal
from lazy_github.ui.screens.primary import LazyGithubMainScreen


class LazyGithub(App):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    async def authenticate_with_github(self):
        try:
            _github = g.github_client()
            self.push_screen(LazyGithubMainScreen())
        except g.GithubAuthenticationRequired:
            log("Triggering auth with github")
            self.push_screen(AuthenticationModal(id="auth-modal"))

    def on_ready(self):
        self.run_worker(self.authenticate_with_github)


app = LazyGithub()
