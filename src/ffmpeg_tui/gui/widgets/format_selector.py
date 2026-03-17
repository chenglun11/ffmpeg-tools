"""Format selector widget: button grid with video/audio format options."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ffmpeg_tui.models.format_config import (
    AUDIO_FORMATS,
    VIDEO_FORMATS,
    FormatInfo,
)

_BTN_STYLE = """
    QPushButton {
        background-color: #f3f4f6;
        color: #374151;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 8px 4px;
        font-size: 13px;
        font-weight: bold;
        min-width: 72px;
        min-height: 32px;
    }
    QPushButton:hover {
        background-color: #ede9fe;
        border-color: #a78bfa;
        color: #6d28d9;
    }
    QPushButton:checked {
        background-color: #7c3aed;
        color: #ffffff;
        border-color: #7c3aed;
    }
"""

_DESC_STYLE = "color: #6b7280; font-size: 12px;"


class FormatSelectorWidget(QWidget):
    """Button-grid selector for output format. Emits *format_changed* with (extension, FormatInfo)."""

    format_changed = pyqtSignal(str, object)  # (extension, FormatInfo)

    def __init__(self, label: str = "输出格式:", parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._formats: list[tuple[str, FormatInfo]] = []
        self._buttons: list[QPushButton] = []
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        # Video formats
        video_group = QGroupBox("视频格式")
        video_grid = QGridLayout(video_group)
        video_grid.setSpacing(6)
        col = 0
        for _vf, info in VIDEO_FORMATS.items():
            btn = QPushButton(info.name)
            btn.setCheckable(True)
            btn.setStyleSheet(_BTN_STYLE)
            btn.setToolTip(info.description)
            video_grid.addWidget(btn, 0, col)
            self._btn_group.addButton(btn, len(self._formats))
            self._formats.append((info.extension, info))
            self._buttons.append(btn)
            col += 1
        layout.addWidget(video_group)

        # Audio formats
        audio_group = QGroupBox("音频格式")
        audio_grid = QGridLayout(audio_group)
        audio_grid.setSpacing(6)
        col = 0
        for _af, info in AUDIO_FORMATS.items():
            btn = QPushButton(info.name)
            btn.setCheckable(True)
            btn.setStyleSheet(_BTN_STYLE)
            btn.setToolTip(info.description)
            audio_grid.addWidget(btn, 0, col)
            self._btn_group.addButton(btn, len(self._formats))
            self._formats.append((info.extension, info))
            self._buttons.append(btn)
            col += 1
        layout.addWidget(audio_group)

        # Codec info label
        self._codec_label = QLabel()
        self._codec_label.setStyleSheet(_DESC_STYLE)
        layout.addWidget(self._codec_label)

        # Default to MP4
        self._buttons[0].setChecked(True)
        self._update_codec_label(0)

        self._btn_group.idClicked.connect(self._on_btn_clicked)

    def _on_btn_clicked(self, btn_id: int) -> None:
        if 0 <= btn_id < len(self._formats):
            ext, info = self._formats[btn_id]
            self._update_codec_label(btn_id)
            self.format_changed.emit(ext, info)

    def _update_codec_label(self, index: int) -> None:
        if 0 <= index < len(self._formats):
            _, info = self._formats[index]
            parts = [info.description]
            codecs = []
            if info.default_video_codec:
                codecs.append(f"视频: {info.default_video_codec}")
            if info.default_audio_codec:
                codecs.append(f"音频: {info.default_audio_codec}")
            if codecs:
                parts.append("  |  ".join(codecs))
            self._codec_label.setText("    ".join(parts))

    def selected_format(self) -> tuple[str, FormatInfo]:
        btn_id = self._btn_group.checkedId()
        if 0 <= btn_id < len(self._formats):
            return self._formats[btn_id]
        return self._formats[0]  # fallback to MP4
