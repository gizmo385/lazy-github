from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container
from textual.coordinate import Coordinate
from textual.screen import ModalScreen
from textual.widgets import DataTable, Markdown, TabbedContent, TabPane
from textual.widgets.data_table import RowDoesNotExist

from lazy_github.lib.bindings import LazyGithubBindings
from lazy_github.lib.constants import BULLET_POINT, CHECKMARK
from lazy_github.lib.context import LazyGithubContext
from lazy_github.lib.github.notifications import fetch_notifications, mark_notification_as_read
from lazy_github.lib.messages import NotificationMarkedAsRead, NotificationSelected
from lazy_github.models.github import Notification
from lazy_github.ui.widgets.common import LazyGithubFooter, SearchableDataTable, TableRow


def notification_to_row(notification: Notification) -> TableRow:
    return (
        notification.updated_at.strftime("%c"),
        notification.subject.subject_type,
        notification.subject.title.strip(),
        notification.reason.replace("_", " ").title(),
        notification.id,
    )


class _NotificationsTableTabPane(TabPane):
    def __init__(self, prefix: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.searchable_table: SearchableDataTable = SearchableDataTable(
            table_id=f"{prefix}_notifications_table",
            search_input_id=f"{prefix}_notifications_table_search_input",
            sort_key="updated_at",
            item_to_key=lambda n: str(n.id),
            item_to_row=notification_to_row,
        )

    def compose(self) -> ComposeResult:
        yield self.searchable_table

    def remove_notification(self, notification: Notification) -> None:
        self.searchable_table.table.remove_row(row_key=str(notification.id))

    def get_selected_notification(self) -> Notification:
        current_row = self.searchable_table.table.cursor_row
        id = self.searchable_table.table.get_cell_at(Coordinate(current_row, self.id_column))
        return self.searchable_table.items[str(id)]

    @on(DataTable.RowSelected)
    def notification_selected(self) -> None:
        notification = self.get_selected_notification()
        self.post_message(NotificationSelected(notification))

    def on_mount(self) -> None:
        self.searchable_table.loading = True
        self.searchable_table.table.cursor_type = "row"
        self.searchable_table.table.add_column("Updated At", key="updated_at")
        self.searchable_table.table.add_column("Subject", key="subject")
        self.searchable_table.table.add_column("Title", key="title")
        self.searchable_table.table.add_column("Reason", key="reason")
        self.searchable_table.table.add_column("Thread ID", key="id")

        self.id_column = self.searchable_table.table.get_column_index("id")


class ReadNotificationTabPane(_NotificationsTableTabPane):
    def __init__(self) -> None:
        super().__init__(id="read", prefix="read", title=f"[green]{CHECKMARK}Read[/green]")


class UnreadNotificationTabPane(_NotificationsTableTabPane):
    BINDINGS = [LazyGithubBindings.MARK_NOTIFICATION_READ]

    def __init__(self) -> None:
        super().__init__(id="unread", prefix="unread", title=f"[red]{BULLET_POINT}Unread[/red]")

    async def action_mark_read(self) -> None:
        current_row = self.searchable_table.table.cursor_row
        id_coord = Coordinate(current_row, self.id_column)
        id = self.searchable_table.table.get_cell_at(id_coord)
        notification_to_mark = self.searchable_table.items[str(id)]

        self.post_message(NotificationMarkedAsRead(notification_to_mark))


class NotificationsContainer(Container):
    DEFAULT_CSS = """
    NotificationsContainer {
        max-height: 80%;
        align: center middle;
    }
    """

    BINDINGS = [LazyGithubBindings.VIEW_READ_NOTIFICATIONS, LazyGithubBindings.VIEW_UNREAD_NOTIFICATIONS]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.unread_tab = UnreadNotificationTabPane()
        self.read_tab = ReadNotificationTabPane()

    def compose(self) -> ComposeResult:
        yield Markdown("# Notifications")
        with TabbedContent():
            yield self.unread_tab
            yield self.read_tab

    @on(NotificationMarkedAsRead)
    async def notification_marked_read(self, message: NotificationMarkedAsRead) -> None:
        await mark_notification_as_read(message.notification)
        try:
            self.unread_tab.remove_notification(message.notification)
            self.read_tab.searchable_table.add_item(message.notification)
        except RowDoesNotExist:
            pass

    def action_view_read(self) -> None:
        self.query_one(TabbedContent).active = "read"
        self.read_tab.searchable_table.table.focus()

    def action_view_unread(self) -> None:
        self.query_one(TabbedContent).active = "unread"
        self.unread_tab.searchable_table.table.focus()

    @work
    async def load_notifications(self) -> None:
        notifications = await fetch_notifications(True)

        unread_count = 0
        for notification in notifications:
            if notification.unread:
                unread_count += 1
                self.unread_tab.searchable_table.add_item(notification)
            else:
                self.read_tab.searchable_table.add_item(notification)

        self.unread_tab.searchable_table.loading = False
        self.read_tab.searchable_table.loading = False

        if unread_count:
            self.action_view_unread()
        else:
            self.action_view_read()

    def on_mount(self) -> None:
        self.load_notifications()


class NotificationsModal(ModalScreen[Notification | None]):
    DEFAULT_CSS = """
    NotificationsModal {
        height: 80%;
        align: center middle;
        content-align: center middle;
    }

    NotificationsContainer {
        min-width: 100;
        max-width: 80%;
        max-height: 50;
        border: thick $background 80%;
        background: $surface-lighten-3;
    }
    """

    BINDINGS = [LazyGithubBindings.CLOSE_DIALOG]

    def compose(self) -> ComposeResult:
        yield NotificationsContainer(id="notifications")
        yield LazyGithubFooter()

    @on(NotificationSelected)
    async def handle_notification_selected(self, message: NotificationSelected) -> None:
        if (
            message.notification.unread
            and LazyGithubContext.config.notifications.mark_notification_as_read_when_selected
        ):
            await mark_notification_as_read(message.notification)
        self.dismiss(message.notification)

    async def action_close(self) -> None:
        self.dismiss()
