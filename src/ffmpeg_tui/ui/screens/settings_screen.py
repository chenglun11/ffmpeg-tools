"""Settings screen for FFmpeg TUI Tools."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from ffmpeg_tui.core.ffmpeg_manager import FFmpegManager


class SettingsScreen(Screen):
    """Settings screen for configuring FFmpeg."""

    BINDINGS = [
        ("escape", "go_back", "返回"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._manager = FFmpegManager()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="settings-container"):
            yield Static("设置 (Settings)", classes="title")
            with Vertical(id="settings-form"):
                yield Static("FFmpeg 配置", classes="subtitle")

                with Vertical(classes="settings-row"):
                    yield Static("FFmpeg 路径:", classes="settings-label")
                    yield Static(self._get_ffmpeg_path(), id="ffmpeg-path", classes="settings-value")

                with Vertical(classes="settings-row"):
                    yield Static("FFmpeg 版本:", classes="settings-label")
                    yield Static(self._get_ffmpeg_version(), id="ffmpeg-version", classes="settings-value")

                with Vertical(classes="settings-row"):
                    yield Static("安装状态:", classes="settings-label")
                    yield Static(self._get_install_status(), id="install-status", classes="settings-value")

                with Vertical(id="settings-buttons"):
                    yield Button("重新检测 FFmpeg", id="btn-detect", variant="primary")
                    yield Button("下载安装 FFmpeg", id="btn-download", variant="success")
                    yield Button("返回主菜单", id="btn-back", variant="default")
        yield Footer()

    def _get_ffmpeg_path(self) -> str:
        path = self._manager.get_ffmpeg_path()
        return str(path) if path else "未找到"

    def _get_ffmpeg_version(self) -> str:
        version = self._manager.get_version()
        return version if version else "未知"

    def _get_install_status(self) -> str:
        if self._manager.check_installation():
            return "[green]已安装[/green]"
        return "[red]未安装[/red]"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-detect":
            self._refresh_status()
        elif event.button.id == "btn-download":
            self._start_download()

    def _refresh_status(self) -> None:
        """Re-detect FFmpeg and update the display."""
        self._manager = FFmpegManager()
        self.query_one("#ffmpeg-path", Static).update(self._get_ffmpeg_path())
        self.query_one("#ffmpeg-version", Static).update(self._get_ffmpeg_version())
        self.query_one("#install-status", Static).update(self._get_install_status())
        self.notify("FFmpeg 检测完成", title="设置")

    def _start_download(self) -> None:
        """Start downloading FFmpeg."""
        self.notify("FFmpeg 下载功能即将完善", title="提示")

    def action_go_back(self) -> None:
        """Return to the main menu."""
        self.app.pop_screen()
