"""Compression parameter panel widget."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from ffmpeg_tui.models.conversion_task import CompressionParams
from ffmpeg_tui.models.ffmpeg_info import QUALITY_PRESETS, RESOLUTION_PRESETS

_AUDIO_BITRATES = ["不更改", "320k", "192k", "128k", "96k"]
_FRAMERATES = ["不更改", "60", "30", "24"]
_ENCODING_PRESETS = [
    "ultrafast",
    "superfast",
    "veryfast",
    "faster",
    "fast",
    "medium",
    "slow",
    "slower",
    "veryslow",
]


class ParameterPanelWidget(QWidget):
    """Form-based panel for configuring video compression parameters.

    Emits *params_changed* whenever any value is modified.
    """

    params_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("压缩参数")
        form = QFormLayout(group)

        # Quality preset
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(["自定义"] + list(QUALITY_PRESETS.keys()))
        form.addRow("质量预设:", self._preset_combo)

        # Resolution
        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems(
            ["不更改"] + [f"{k} ({v})" for k, v in RESOLUTION_PRESETS.items()]
        )
        form.addRow("分辨率:", self._resolution_combo)

        # Video bitrate
        self._video_bitrate = QLineEdit()
        self._video_bitrate.setPlaceholderText("例如: 4000k 或 5M")
        form.addRow("视频码率:", self._video_bitrate)

        # Audio bitrate
        self._audio_bitrate_combo = QComboBox()
        self._audio_bitrate_combo.addItems(_AUDIO_BITRATES)
        form.addRow("音频码率:", self._audio_bitrate_combo)

        # Framerate
        self._framerate_combo = QComboBox()
        self._framerate_combo.addItems(_FRAMERATES)
        form.addRow("帧率:", self._framerate_combo)

        # Encoding preset
        self._encoding_preset_combo = QComboBox()
        self._encoding_preset_combo.addItems(_ENCODING_PRESETS)
        self._encoding_preset_combo.setCurrentText("medium")
        form.addRow("编码预设:", self._encoding_preset_combo)

        outer.addWidget(group)

        # Connect signals
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        self._resolution_combo.currentIndexChanged.connect(lambda _: self.params_changed.emit())
        self._video_bitrate.textChanged.connect(lambda _: self.params_changed.emit())
        self._audio_bitrate_combo.currentIndexChanged.connect(lambda _: self.params_changed.emit())
        self._framerate_combo.currentIndexChanged.connect(lambda _: self.params_changed.emit())
        self._encoding_preset_combo.currentIndexChanged.connect(
            lambda _: self.params_changed.emit()
        )

    def _on_preset_changed(self, text: str) -> None:
        if text in QUALITY_PRESETS:
            params = QUALITY_PRESETS[text]
            self._video_bitrate.setText(params.video_bitrate or "")
            if params.audio_bitrate and params.audio_bitrate in _AUDIO_BITRATES:
                self._audio_bitrate_combo.setCurrentText(params.audio_bitrate)
            self._encoding_preset_combo.setCurrentText(params.preset)
        self.params_changed.emit()

    def get_params(self) -> CompressionParams:
        """Return the currently configured compression parameters."""
        # Resolution
        resolution = None
        res_text = self._resolution_combo.currentText()
        if res_text != "不更改":
            for key, value in RESOLUTION_PRESETS.items():
                if res_text.startswith(key):
                    resolution = value
                    break

        # Video bitrate
        video_bitrate = self._video_bitrate.text().strip() or None

        # Audio bitrate
        audio_bitrate = None
        ab_text = self._audio_bitrate_combo.currentText()
        if ab_text != "不更改":
            audio_bitrate = ab_text

        # Framerate
        framerate = None
        fr_text = self._framerate_combo.currentText()
        if fr_text != "不更改":
            framerate = float(fr_text)

        # Encoding preset
        preset = self._encoding_preset_combo.currentText()

        return CompressionParams(
            resolution=resolution,
            video_bitrate=video_bitrate,
            audio_bitrate=audio_bitrate,
            framerate=framerate,
            preset=preset,
        )
