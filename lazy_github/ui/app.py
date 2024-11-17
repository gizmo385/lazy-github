from textual import log
from textual.app import App
from textual.theme import Theme

from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.github.auth import GithubAuthenticationRequired
from lazy_github.lib.messages import SettingsModalDismissed
from lazy_github.ui.screens.auth import AuthenticationModal
from lazy_github.ui.screens.primary import LazyGithubMainScreen


class LazyGithub(App):
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("q", "quit", "Quit"), ("ctrl+p", "command_palette")]

    async def authenticate_with_github(self):
        try:
            # We pull the user here to validate auth
            _ = await LazyGithubContext.client.user()
            self.push_screen(LazyGithubMainScreen(id="main-screen"))
        except GithubAuthenticationRequired:
            log("Triggering auth with github")
            self.push_screen(AuthenticationModal(id="auth-modal"))

    async def on_ready(self):
        await self.authenticate_with_github()

    def on_settings_modal_dismissed(self, message: SettingsModalDismissed) -> None:
        if not message.changed:
            return

        self.notify("Settings updated")
        if isinstance(LazyGithubContext.config.appearance.theme, Theme):
            self.theme = LazyGithubContext.config.appearance.theme.name
        else:
            self.theme = LazyGithubContext.config.appearance.theme

        self.query_one("#main-screen", LazyGithubMainScreen).handle_settings_update()

    def on_mount(self) -> None:
        self.theme = LazyGithubContext.config.appearance.theme.name


app = LazyGithub()
