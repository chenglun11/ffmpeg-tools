"""Settings tab: FFmpeg status, detection, and download."""

from typing import Optional

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ffmpeg_tui import __version__
from ffmpeg_tui.core.ffmpeg_manager import FFmpegManager
from ffmpeg_tui.utils.file_utils import format_file_size

from ..worker import DownloadWorker, UpdateCheckWorker


class SettingsTab(QWidget):
    ffmpeg_status_changed = pyqtSignal()

    def __init__(self, manager: FFmpegManager, parent=None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._download_worker: Optional[DownloadWorker] = None
        self._update_worker: Optional[UpdateCheckWorker] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # FFmpeg info group
        group = QGroupBox("FFmpeg 状态")
        form = QFormLayout(group)

        self._status_label = QLabel()
        form.addRow("安装状态:", self._status_label)

        self._path_label = QLabel()
        self._path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        form.addRow("路径:", self._path_label)

        self._version_label = QLabel()
        self._version_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        form.addRow("版本:", self._version_label)

        layout.addWidget(group)

        # Buttons
        btn_row = QHBoxLayout()
        self._detect_btn = QPushButton("重新检测")
        self._download_btn = QPushButton("下载安装 FFmpeg")
        self._download_btn.setObjectName("primaryBtn")
        btn_row.addWidget(self._detect_btn)
        btn_row.addWidget(self._download_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Download progress
        self._dl_progress = QProgressBar()
        self._dl_progress.setRange(0, 100)
        self._dl_progress.hide()
        layout.addWidget(self._dl_progress)

        self._dl_status_label = QLabel()
        self._dl_status_label.hide()
        layout.addWidget(self._dl_status_label)

        # Software update group
        update_group = QGroupBox("软件更新")
        update_form = QFormLayout(update_group)

        self._cur_ver_label = QLabel(__version__)
        update_form.addRow("当前版本:", self._cur_ver_label)

        self._latest_ver_label = QLabel("-")
        update_form.addRow("最新版本:", self._latest_ver_label)

        self._release_notes_label = QLabel()
        self._release_notes_label.setWordWrap(True)
        self._release_notes_label.hide()
        update_form.addRow("更新说明:", self._release_notes_label)

        layout.addWidget(update_group)

        update_btn_row = QHBoxLayout()
        self._check_update_btn = QPushButton("检查更新")
        self._goto_download_btn = QPushButton("前往下载")
        self._goto_download_btn.setObjectName("successBtn")
        self._goto_download_btn.hide()
        update_btn_row.addWidget(self._check_update_btn)
        update_btn_row.addWidget(self._goto_download_btn)
        update_btn_row.addStretch()
        layout.addLayout(update_btn_row)

        self._update_status_label = QLabel()
        self._update_status_label.hide()
        layout.addWidget(self._update_status_label)

        layout.addStretch()

        # Connections
        self._detect_btn.clicked.connect(self._refresh)
        self._download_btn.clicked.connect(self._download)
        self._check_update_btn.clicked.connect(self._check_update)
        self._goto_download_btn.clicked.connect(self._open_download_url)

        self._download_url: str = ""
        self._refresh()

    def _refresh(self) -> None:
        installed = self._manager.check_installation()
        if installed:
            self._status_label.setText("已安装")
            self._status_label.setStyleSheet("color: green; font-weight: bold;")
            path = self._manager.get_ffmpeg_path()
            path_str = str(path) if path else "-"
            self._path_label.setText(path_str)
            self._path_label.setToolTip(path_str)
            version = self._manager.get_version() or "-"
            first_line = version.split("\n")[0].strip()
            self._version_label.setText(first_line)
            self._version_label.setToolTip(version)
            self._download_btn.setEnabled(False)
        else:
            self._status_label.setText("未安装")
            self._status_label.setStyleSheet("color: red; font-weight: bold;")
            self._path_label.setText("-")
            self._version_label.setText("-")
            self._download_btn.setEnabled(True)

        self.ffmpeg_status_changed.emit()

    def _download(self) -> None:
        self._download_btn.setEnabled(False)
        self._detect_btn.setEnabled(False)
        self._dl_progress.setValue(0)
        self._dl_progress.show()
        self._dl_status_label.setText("正在下载…")
        self._dl_status_label.show()

        self._download_worker = DownloadWorker()
        self._download_worker.progress.connect(self._on_dl_progress)
        self._download_worker.finished.connect(self._on_dl_finished)
        self._download_worker.start()

    def _on_dl_progress(self, downloaded: int, total: int) -> None:
        if total > 0:
            pct = int(downloaded / total * 100)
            self._dl_progress.setValue(pct)
            self._dl_status_label.setText(
                f"下载中: {format_file_size(downloaded)} / {format_file_size(total)}"
            )
        else:
            self._dl_status_label.setText(f"下载中: {format_file_size(downloaded)}")

    def _on_dl_finished(self, success: bool, message: str) -> None:
        self._detect_btn.setEnabled(True)
        if success:
            self._dl_status_label.setText("下载完成!")
            self._dl_status_label.setStyleSheet("color: green;")
            self._refresh()
        else:
            self._dl_status_label.setText(f"下载失败: {message}")
            self._dl_status_label.setStyleSheet("color: red;")
            self._download_btn.setEnabled(True)
            QMessageBox.critical(self, "下载失败", message)

    # -- Update check ----------------------------------------------------------

    def _check_update(self) -> None:
        self._check_update_btn.setEnabled(False)
        self._update_status_label.setText("正在检查…")
        self._update_status_label.setStyleSheet("")
        self._update_status_label.show()
        self._goto_download_btn.hide()
        self._release_notes_label.hide()

        self._update_worker = UpdateCheckWorker()
        self._update_worker.finished.connect(self._on_update_result)
        self._update_worker.error.connect(self._on_update_error)
        self._update_worker.start()

    def _on_update_result(self, has_update: bool, info: object) -> None:
        self._check_update_btn.setEnabled(True)

        if info is None:
            # Error already shown via _on_update_error
            if not self._update_status_label.text().startswith("检查失败"):
                self._latest_ver_label.setText("-")
                self._update_status_label.setText("检查失败，请稍后重试")
                self._update_status_label.setStyleSheet("color: red;")
        elif has_update:
            self._latest_ver_label.setText(info.latest_version)
            self._update_status_label.setText("发现新版本!")
            self._update_status_label.setStyleSheet("color: green;")
            self._download_url = info.download_url
            self._goto_download_btn.show()
            if info.release_notes:
                self._release_notes_label.setText(info.release_notes[:500])
                self._release_notes_label.show()
        else:
            self._latest_ver_label.setText(__version__)
            self._update_status_label.setText("已是最新版本")
            self._update_status_label.setStyleSheet("color: green;")

    def _on_update_error(self, message: str) -> None:
        self._latest_ver_label.setText("-")
        self._update_status_label.setText(f"检查失败: {message}")
        self._update_status_label.setStyleSheet("color: red;")

    def _open_download_url(self) -> None:
        if self._download_url:
            QDesktopServices.openUrl(QUrl(self._download_url))
