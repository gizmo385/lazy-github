import enum
from typing import Any

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from textual.app import ComposeResult, on
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Input, Markdown, Rule, Select, Static, Switch

from lazy_github.lib.config import Config


def field_name_to_readable_name(name: str) -> str:
    return name.replace("_", " ").title()


class FieldName(Static):
    pass


class FieldSetting(Container):
    DEFAULT_CSS = """
    FieldSetting {
        layout: grid;
        grid-size: 2;
        height: 3;
    }

    FieldName {
        width: auto;
        align: right middle;
    }

    Input {
        width: 70;
    }
    """

    def _field_to_widget(self) -> Widget:
        id = f"adjust_{self.field_name}_input"
        if self.field.annotation is bool:
            # If the setting is a boolean, render a on/off switch
            return Switch(value=self.value, id=id)
        elif isinstance(self.field.annotation, type) and issubclass(self.field.annotation, enum.StrEnum):
            # If the setting is an enum, then we'll render a dropdown with all of the available options
            result = Select(options=[(t.title(), t) for t in list(self.field.annotation)], value=self.value, id=id)
            return result
        else:
            return Input(value=str(self.value), id=id)

    def __init__(self, field_name: str, field: FieldInfo, value: Any) -> None:
        super().__init__()
        self.field_name = field_name
        self.field = field
        self.value = value

    def compose(self) -> ComposeResult:
        yield FieldName(f"{field_name_to_readable_name(self.field_name)}:")
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
        yield Markdown(f"## {field_name_to_readable_name(self.parent_field_name)}")
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

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config

    def compose(self) -> ComposeResult:
        yield Markdown("# LazyGithub Settings")
        with ScrollableContainer(id="settings_adjustment"):
            for field, value in self.config:
                yield SettingsSection(field, value)

        yield Rule()

        with Horizontal(id="settings_buttons"):
            yield Button("Save", id="save_settings", variant="success")
            yield Button("Cancel", id="cancel_settings", variant="error")

    def _build_updated_settings(self):
        pass

    @on(Button.Pressed, "#save_settings")
    async def save_settings(self, _: Button.Pressed) -> None:
        self.notify("Settings saved")
        self.app.pop_screen()

    @on(Button.Pressed, "#cancel_settings")
    async def cancel_settings(self, _: Button.Pressed) -> None:
        self.app.pop_screen()


class SettingsModal(ModalScreen):
    DEFAULT_CSS = """
    SettingsModal {
        height: 80%;
    }

    SettingsContainer {
        width: 100;
        height: 50;
        border: thick $background 80%;
        background: $surface;
    }
    """

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config

    def compose(self) -> ComposeResult:
        yield SettingsContainer(self.config)


if __name__ == "__main__":
    from textual.app import App

    class SettingsMain(App):
        def compose(self) -> ComposeResult:
            yield SettingsContainer(Config.load_config())

    SettingsMain().run()
