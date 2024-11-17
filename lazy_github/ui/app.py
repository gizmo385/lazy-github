from textual import log
from textual.app import App
from textual.theme import Theme

from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.github.auth import GithubAuthenticationRequired
from lazy_github.lib.messages import SettingsModalDismissed
from lazy_github.ui.screens.auth import AuthenticationModal
from lazy_github.ui.screens.primary import LazyGithubMainScreen


class LazyGithub(App):
    BINDINGS = [("q", "quit", "Quit"), ("ctrl+p", "command_palette"), ("ctrl+m", "maximize", "Maximize")]

    has_shown_maximize_toast: bool = False

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

    def action_maximize(self) -> None:
        if self.screen.is_maximized:
            return
        if self.screen.focused is not None:
            # We don't need to repeatedly show this to the user
            if self.screen.maximize(self.screen.focused) and not self.has_shown_maximize_toast:
                self.notify("Current view maximized. Press [b]escape[/b] to return.", title="View Maximized")
                self.has_shown_maximize_toast = True


app = LazyGithub()
