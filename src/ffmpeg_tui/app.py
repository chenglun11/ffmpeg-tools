"""FFmpeg TUI application."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer


class FFmpegTUIApp(App):
    """FFmpeg TUI Tools main application."""

    TITLE = "FFmpeg TUI Tools"
    CSS_PATH = "ui/styles/main.tcss"

    BINDINGS = [
        ("q", "quit", "退出"),
    ]

    def on_mount(self) -> None:
        """Push the main screen on startup."""
        from ffmpeg_tui.ui.screens.main_screen import MainScreen

        self.push_screen(MainScreen())
