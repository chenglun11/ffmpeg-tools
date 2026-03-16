"""Main application window with tab-based navigation."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QTabWidget,
)

from ffmpeg_tui.core.ffmpeg_manager import FFmpegManager

from .tabs.compress_tab import CompressTab
from .tabs.convert_tab import ConvertTab
from .tabs.settings_tab import SettingsTab
from .worker import UpdateCheckWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._manager = FFmpegManager()

        self.setWindowTitle("FFmpeg Tools")
        self.resize(800, 600)

        # Tabs
        self._tabs = QTabWidget()
        self._convert_tab = ConvertTab(self._manager)
        self._compress_tab = CompressTab(self._manager)
        self._settings_tab = SettingsTab(self._manager)

        self._tabs.addTab(self._convert_tab, "格式转换")
        self._tabs.addTab(self._compress_tab, "视频压缩")
        self._tabs.addTab(self._settings_tab, "设置")

        self.setCentralWidget(self._tabs)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        # Connect settings tab signal to refresh status
        self._settings_tab.ffmpeg_status_changed.connect(self._update_status)

        self._update_status()
        self._silent_update_check()

    def _update_status(self) -> None:
        if self._manager.check_installation():
            version = self._manager.get_version() or "unknown"
            first_line = version.split("\n")[0] if version else "unknown"
            self._status_bar.showMessage(f"FFmpeg: {first_line}")
        else:
            self._status_bar.showMessage("FFmpeg: 未安装")

    def _silent_update_check(self) -> None:
        self._update_worker = UpdateCheckWorker()
        self._update_worker.finished.connect(self._on_silent_update_result)
        self._update_worker.start()

    def _on_silent_update_result(self, has_update: bool, info: object) -> None:
        if has_update and info is not None:
            self._status_bar.showMessage(
                f"FFmpeg Tools v{info.latest_version} 可用，请前往设置页更新",
                10000,
            )
