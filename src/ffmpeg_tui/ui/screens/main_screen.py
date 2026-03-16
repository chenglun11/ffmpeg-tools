"""Main menu screen for FFmpeg TUI Tools."""

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList, Static
from textual.widgets.option_list import Option

from ffmpeg_tui.core.ffmpeg_manager import FFmpegManager

ASCII_ART = r"""
 _____ _____                          _____ _   _ ___
|  ___|  ___|                        |_   _| | | |_ _|
| |_  | |_ _ __ ___  _ __   ___  __ _ | | | | | || |
|  _| |  _| '_ ` _ \| '_ \ / _ \/ _` || | | | | || |
| |   | | | | | | | | |_) |  __/ (_| || | | |_| || |
\_|   \_| |_| |_| |_| .__/ \___|\__, |\_/  \___/|___|
                     | |          __/ |
                     |_|         |___/
"""

MENU_OPTIONS = [
    ("1. 格式转换 (Format Convert)", "convert"),
    ("2. 视频压缩 (Video Compress)", "compress"),
    ("3. 设置 (Settings)", "settings"),
    ("4. 退出 (Quit)", "quit"),
]


class MainScreen(Screen):
    """Main menu screen."""

    BINDINGS = [
        ("1", "menu_select('convert')", "格式转换"),
        ("2", "menu_select('compress')", "视频压缩"),
        ("3", "menu_select('settings')", "设置"),
        ("4", "quit", "退出"),
        ("q", "quit", "退出"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-content"):
            yield Static(ASCII_ART, id="ascii-art")
            yield Static(self._get_ffmpeg_status(), id="ffmpeg-status")
            with Center():
                yield OptionList(
                    *[Option(label, id=opt_id) for label, opt_id in MENU_OPTIONS],
                    id="menu-list",
                )
        yield Static("使用 ↑↓ 选择菜单项，Enter 确认，或按数字键快速选择", classes="status-bar")
        yield Footer()

    def _get_ffmpeg_status(self) -> str:
        """Check FFmpeg installation and return a status string."""
        manager = FFmpegManager()
        if manager.check_installation():
            version = manager.get_version() or "未知版本"
            path = manager.get_ffmpeg_path()
            return f"FFmpeg: [green]已安装[/green]  |  {version}\n路径: {path}"
        return "FFmpeg: [red]未安装[/red]  |  请进入设置安装 FFmpeg"

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle menu item selection."""
        option_id = event.option_id
        if option_id == "quit":
            self.app.exit()
        elif option_id == "settings":
            from ffmpeg_tui.ui.screens.settings_screen import SettingsScreen

            self.app.push_screen(SettingsScreen())
        elif option_id == "convert":
            from ffmpeg_tui.ui.screens.convert_screen import ConvertScreen

            self.app.push_screen(ConvertScreen())
        elif option_id == "compress":
            from ffmpeg_tui.ui.screens.compress_screen import CompressScreen

            self.app.push_screen(CompressScreen())

    def action_menu_select(self, action: str) -> None:
        """Handle keyboard shortcut menu selection."""
        if action == "quit":
            self.app.exit()
        elif action == "settings":
            from ffmpeg_tui.ui.screens.settings_screen import SettingsScreen

            self.app.push_screen(SettingsScreen())
        elif action == "convert":
            from ffmpeg_tui.ui.screens.convert_screen import ConvertScreen

            self.app.push_screen(ConvertScreen())
        elif action == "compress":
            from ffmpeg_tui.ui.screens.compress_screen import CompressScreen

            self.app.push_screen(CompressScreen())
