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
from .tabs.meta_tab import MetaTab
from .tabs.settings_tab import SettingsTab
from .worker import UpdateCheckWorker

_STYLESHEET = """
QMainWindow {
    background-color: #ffffff;
}
QTabWidget::pane {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    background-color: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background-color: #f5f5f5;
    color: #555555;
    padding: 10px 24px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #e0e0e0;
    border-bottom: none;
    font-size: 13px;
    min-width: 80px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #7c3aed;
    border-bottom: 2px solid #7c3aed;
}
QTabBar::tab:hover:!selected {
    background-color: #ede9fe;
    color: #6d28d9;
}
QWidget {
    background-color: #ffffff;
    color: #1f2937;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
    font-size: 13px;
    color: #7c3aed;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #ffffff;
}
QLabel {
    color: #374151;
    font-size: 13px;
}
QLineEdit {
    background-color: #f9fafb;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 6px 10px;
    color: #1f2937;
    font-size: 13px;
    selection-background-color: #c4b5fd;
}
QLineEdit:focus {
    border-color: #7c3aed;
    background-color: #ffffff;
}
QLineEdit::placeholder {
    color: #9ca3af;
}
QPushButton {
    background-color: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 7px 18px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #e5e7eb;
    border-color: #9ca3af;
}
QPushButton:pressed {
    background-color: #d1d5db;
}
QPushButton:disabled {
    background-color: #f9fafb;
    color: #9ca3af;
    border-color: #e5e7eb;
}
QPushButton#primaryBtn {
    background-color: #7c3aed;
    color: #ffffff;
    border: none;
    font-size: 14px;
    padding: 9px 24px;
}
QPushButton#primaryBtn:hover {
    background-color: #6d28d9;
}
QPushButton#primaryBtn:pressed {
    background-color: #5b21b6;
}
QPushButton#primaryBtn:disabled {
    background-color: #c4b5fd;
    color: #ede9fe;
}
QPushButton#successBtn {
    background-color: #10b981;
    color: #ffffff;
    border: none;
}
QPushButton#successBtn:hover {
    background-color: #059669;
}
QProgressBar {
    background-color: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    text-align: center;
    color: #374151;
    font-size: 12px;
    min-height: 18px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed, stop:1 #a78bfa);
    border-radius: 5px;
}
QStatusBar {
    background-color: #f9fafb;
    color: #6b7280;
    border-top: 1px solid #e5e7eb;
    font-size: 12px;
    padding: 2px 8px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._manager = FFmpegManager()

        self.setWindowTitle("FFmpeg Tools")
        self.resize(860, 640)
        self.setStyleSheet(_STYLESHEET)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setElideMode(Qt.TextElideMode.ElideNone)
        self._tabs.setUsesScrollButtons(False)

        self._convert_tab = ConvertTab(self._manager)
        self._compress_tab = CompressTab(self._manager)
        self._meta_tab = MetaTab(self._manager)
        self._settings_tab = SettingsTab(self._manager)

        self._tabs.addTab(self._convert_tab, "格式转换")
        self._tabs.addTab(self._compress_tab, "视频压缩")
        self._tabs.addTab(self._meta_tab, "Meta 专版")
        self._tabs.addTab(self._settings_tab, "设置")

        self.setCentralWidget(self._tabs)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        # Connect settings tab signal to refresh status
        self._settings_tab.ffmpeg_status_changed.connect(self._update_status)
        self._settings_tab.ffmpeg_status_changed.connect(self._update_tabs_state)

        self._update_status()
        self._update_tabs_state()
        self._silent_update_check()

    def _update_status(self) -> None:
        if self._manager.check_installation():
            version = self._manager.get_version() or "unknown"
            first_line = version.split("\n")[0] if version else "unknown"
            self._status_bar.showMessage(f"FFmpeg: {first_line}")
        else:
            self._status_bar.showMessage("FFmpeg: 未安装 — 请前往设置页安装")

    def _update_tabs_state(self) -> None:
        """Enable/disable tabs based on FFmpeg installation status."""
        installed = self._manager.check_installation()
        for tab in (self._convert_tab, self._compress_tab, self._meta_tab):
            start_btn = getattr(tab, "_start_btn", None)
            if start_btn:
                start_btn.setEnabled(installed)
                if not installed:
                    start_btn.setToolTip("请先在设置页安装 FFmpeg")

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

    def closeEvent(self, event) -> None:
        # Stop any running background workers before closing.
        # Workers may already be deleted via deleteLater, so guard with
        # try/except to avoid RuntimeError on destroyed C++ objects.
        try:
            for tab in (self._convert_tab, self._compress_tab, self._meta_tab):
                worker = getattr(tab, "_worker", None)
                if worker is not None:
                    try:
                        if worker.isRunning():
                            worker.cancel()
                            worker.wait(3000)
                    except RuntimeError:
                        pass
            if hasattr(self, "_update_worker"):
                try:
                    if self._update_worker.isRunning():
                        self._update_worker.quit()
                        self._update_worker.wait(2000)
                except RuntimeError:
                    pass
        except Exception:
            pass
        super().closeEvent(event)
