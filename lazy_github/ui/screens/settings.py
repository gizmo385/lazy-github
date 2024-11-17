import enum
from typing import Any

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.theme import BUILTIN_THEMES, Theme
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Markdown, Rule, Select, Switch

from lazy_github.lib.messages import SettingsModalDismissed
from lazy_github.lib.context import LazyGithubContext

# There are certain fields that we don't actually want to expose through this settings UI, because it is modifiable
# through more obvious means elsewhere
_SECTIONS_TO_SKIP = {"repositories"}


def _field_name_to_readable_name(name: str) -> str:
    return name.replace("_", " ").title()


def _id_for_field_input(field_name: str) -> str:
    return f"adjust_{field_name}_input"


class FieldSetting(Container):
    DEFAULT_CSS = """
    FieldSetting {
        layout: grid;
        grid-size: 2;
        height: 3;
    }

    Input {
        width: 70;
    }
    """

    def _field_to_widget(self) -> Widget:
        id = _id_for_field_input(self.field_name)
        if self.field.annotation is bool:
            # If the setting is a boolean, render a on/off switch
            return Switch(value=self.value, id=id)
        elif isinstance(self.field.annotation, type) and issubclass(self.field.annotation, enum.StrEnum):
            # If the setting is an enum, then we'll render a dropdown with all of the available options
            return Select(options=[(t.title(), t) for t in list(self.field.annotation)], value=self.value, id=id)
        elif isinstance(self.field.annotation, type) and issubclass(self.field.annotation, Theme):
            theme_options = [(t.title().replace("-", " "), t) for t in BUILTIN_THEMES.keys()]
            if isinstance(self.value, Theme):
                return Select(options=theme_options, value=self.value.name, id=id)
            else:
                return Select(options=theme_options, value=self.value, id=id)
        else:
            # If no other input mechanism fits, then we'll fallback to just a raw string input field
            return Input(value=str(self.value), id=id)

    def __init__(self, field_name: str, field: FieldInfo, value: Any) -> None:
        super().__init__()
        self.field_name = field_name
        self.field = field
        self.value = value

    def compose(self) -> ComposeResult:
        yield Label(f"{_field_name_to_readable_name(self.field_name)}:")
        yield self._field_to_widget()


class SettingsSection(Vertical):
    DEFAULT_CSS = """
    SettingsSection {
        border: blank white;
        height: auto;
    }
    """

    def __init__(self, parent_field_name: str, model: BaseModel) -> None:
        super().__init__()
        self.parent_field_name = parent_field_name
        self.model = model
        self.fields = model.model_fields

    def compose(self) -> ComposeResult:
        yield Markdown(f"## {_field_name_to_readable_name(self.parent_field_name)}")
        for field_name, field_info in self.fields.items():
            current_value = getattr(self.model, field_name)
            yield FieldSetting(field_name, field_info, current_value)


class SettingsContainer(Container):
    DEFAULT_CSS = """
    SettingsContainer {
        dock: top;
        height: 80%;
        align: center middle;
    }

    #settings_buttons {
        width: auto;
        height: auto;
        padding-left: 35;
    }
    """

    BINDINGS = [
        ("shift+enter", "save_settings", "Save settings"),
        ("q", "exit_settings", "Exit settings"),
    ]

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Markdown("# LazyGithub Settings")
        with ScrollableContainer(id="settings_adjustment"):
            for field, value in LazyGithubContext.config:
                if field in _SECTIONS_TO_SKIP:
                    continue
                yield SettingsSection(field, value)

        yield Rule()

        with Horizontal(id="settings_buttons"):
            yield Button("Save", id="save_settings", variant="success")
            yield Button("Cancel", id="cancel_settings", variant="error")

    def _update_settings(self):
        with LazyGithubContext.config.to_edit() as updated_config:
            for _, model in updated_config:
                if not isinstance(model, BaseModel):
                    continue

                for field_name, _ in model:
                    value_adjustment_id = _id_for_field_input(field_name)
                    try:
                        updated_value_input = self.query_one(f"#{value_adjustment_id}")
                    except NoMatches:
                        # If there isn't a way to adjust this setting, skip it
                        continue

                    if not isinstance(updated_value_input, (Switch, Input, Select)):
                        raise TypeError(
                            f"Unexpected value input type: {type(updated_value_input)}. Please file an issue"
                        )

                    setattr(model, field_name, updated_value_input.value)

    @on(Button.Pressed, "#save_settings")
    async def save_settings(self, _: Button.Pressed) -> None:
        self._update_settings()
        self.post_message(SettingsModalDismissed(True))

    async def action_save_settings(self) -> None:
        self._update_settings()
        self.post_message(SettingsModalDismissed(True))

    @on(Button.Pressed, "#cancel_settings")
    async def cancel_settings(self, _: Button.Pressed) -> None:
        self.post_message(SettingsModalDismissed(False))

    async def action_exit_settings(self) -> None:
        self.post_message(SettingsModalDismissed(False))


class SettingsModal(ModalScreen):
    DEFAULT_CSS = """
    SettingsModal {
        height: 80%;
    }

    SettingsContainer {
        width: 100;
        height: 50;
        border: thick $background 80%;
        background: $surface-lighten-3;
    }
    """

    def on_settings_modal_dismissed(self, _: SettingsModalDismissed) -> None:
        self.dismiss()

    def compose(self) -> ComposeResult:
        yield SettingsContainer()
