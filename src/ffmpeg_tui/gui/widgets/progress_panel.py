"""Progress display panel with bar, details, and cancel button."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ffmpeg_tui.utils.file_utils import format_duration


class ProgressPanelWidget(QWidget):
    """Progress bar + detail labels + cancel button.

    Emits *cancel_clicked* when the user presses the cancel button.
    """

    cancel_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Progress bar row
        bar_row = QHBoxLayout()
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._pct_label = QLabel("0%")
        bar_row.addWidget(self._progress_bar, stretch=1)
        bar_row.addWidget(self._pct_label)
        layout.addLayout(bar_row)

        # Details row
        detail_row = QHBoxLayout()
        self._frame_label = QLabel("帧: -")
        self._fps_label = QLabel("FPS: -")
        self._speed_label = QLabel("速度: -")
        self._eta_label = QLabel("ETA: -")
        detail_row.addWidget(self._frame_label)
        detail_row.addWidget(self._fps_label)
        detail_row.addWidget(self._speed_label)
        detail_row.addWidget(self._eta_label)
        detail_row.addStretch()
        layout.addLayout(detail_row)

        # Status / cancel row
        status_row = QHBoxLayout()
        self._status_label = QLabel()
        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self.cancel_clicked.emit)
        status_row.addWidget(self._status_label, stretch=1)
        status_row.addWidget(self._cancel_btn)
        layout.addLayout(status_row)

        self.hide()

    def reset(self) -> None:
        self._progress_bar.setValue(0)
        self._pct_label.setText("0%")
        self._frame_label.setText("帧: -")
        self._fps_label.setText("FPS: -")
        self._speed_label.setText("速度: -")
        self._eta_label.setText("ETA: -")
        self._status_label.setText("")
        self._cancel_btn.setEnabled(True)
        self.show()

    def update_progress(
        self,
        percentage: float,
        frame: int,
        fps: float,
        speed: float,
        eta_seconds: float,
    ) -> None:
        pct = min(int(percentage), 100)
        self._progress_bar.setValue(pct)
        self._pct_label.setText(f"{pct}%")
        self._frame_label.setText(f"帧: {frame}")
        self._fps_label.setText(f"FPS: {fps:.1f}")
        self._speed_label.setText(f"速度: {speed:.2f}x")
        eta_str = format_duration(eta_seconds) if eta_seconds > 0 else "-"
        self._eta_label.setText(f"ETA: {eta_str}")

    def set_completed(self, success: bool, message: str = "") -> None:
        self._cancel_btn.setEnabled(False)
        if success:
            self._progress_bar.setValue(100)
            self._pct_label.setText("100%")
            self._status_label.setText(message or "完成!")
            self._status_label.setStyleSheet("color: green;")
        else:
            self._status_label.setText(message or "失败")
            self._status_label.setStyleSheet("color: red;")

    def set_cancelled(self) -> None:
        self._cancel_btn.setEnabled(False)
        self._status_label.setText("已取消")
        self._status_label.setStyleSheet("color: orange;")
