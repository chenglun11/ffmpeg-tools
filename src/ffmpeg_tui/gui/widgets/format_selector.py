"""Format selector widget: QComboBox with video/audio format options."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from ffmpeg_tui.models.format_config import (
    AUDIO_FORMATS,
    VIDEO_FORMATS,
    FormatInfo,
)


class FormatSelectorWidget(QWidget):
    """Drop-down selector for output format. Emits *format_changed* with (extension, FormatInfo)."""

    format_changed = pyqtSignal(str, object)  # (extension, FormatInfo)

    def __init__(self, label: str = "输出格式:", parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(label)
        self._combo = QComboBox()
        self._codec_label = QLabel()

        layout.addWidget(self._label)
        layout.addWidget(self._combo, stretch=1)
        layout.addWidget(self._codec_label)

        # Populate
        self._formats: list[tuple[str, FormatInfo]] = []
        self._combo.addItem("── 视频格式 ──")
        self._formats.append(("", FormatInfo(name="", extension="", description="")))
        for vf, info in VIDEO_FORMATS.items():
            self._combo.addItem(f"{info.name} - {info.description}")
            self._formats.append((info.extension, info))

        self._combo.addItem("── 音频格式 ──")
        self._formats.append(("", FormatInfo(name="", extension="", description="")))
        for af, info in AUDIO_FORMATS.items():
            self._combo.addItem(f"{info.name} - {info.description}")
            self._formats.append((info.extension, info))

        # Disable separator items
        model = self._combo.model()
        for idx in (0, len(VIDEO_FORMATS) + 1):
            item = model.item(idx)
            if item:
                item.setEnabled(False)

        self._combo.setCurrentIndex(1)  # default to MP4
        self._update_codec_label(1)

        self._combo.currentIndexChanged.connect(self._on_index_changed)

    def _on_index_changed(self, index: int) -> None:
        if 0 <= index < len(self._formats):
            ext, info = self._formats[index]
            if ext:  # skip separator rows
                self._update_codec_label(index)
                self.format_changed.emit(ext, info)

    def _update_codec_label(self, index: int) -> None:
        if 0 <= index < len(self._formats):
            _, info = self._formats[index]
            parts = []
            if info.default_video_codec:
                parts.append(f"V: {info.default_video_codec}")
            if info.default_audio_codec:
                parts.append(f"A: {info.default_audio_codec}")
            self._codec_label.setText("  ".join(parts))

    def selected_format(self) -> tuple[str, FormatInfo]:
        idx = self._combo.currentIndex()
        if 0 <= idx < len(self._formats):
            return self._formats[idx]
        return self._formats[1]  # fallback to MP4
