"""Compression parameter panel widget — button-group based."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ffmpeg_tui.models.conversion_task import CompressionParams
from ffmpeg_tui.models.ffmpeg_info import QUALITY_PRESETS, RESOLUTION_PRESETS

_BTN_STYLE = """
    QPushButton {
        background-color: #f3f4f6;
        color: #374151;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: bold;
        min-width: 54px;
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

_SHORTCUT_BTN_STYLE = """
    QPushButton {
        background-color: #f9fafb;
        color: #6b7280;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
        min-width: 40px;
    }
    QPushButton:hover {
        background-color: #ede9fe;
        color: #7c3aed;
        border-color: #7c3aed;
    }
    QPushButton:pressed {
        background-color: #ddd6fe;
    }
"""

_AUDIO_BITRATES = ["不更改", "320k", "192k", "128k", "96k"]
_FRAMERATES = ["不更改", "60", "30", "24"]
_ENCODING_PRESETS = ["ultrafast", "veryfast", "fast", "medium", "slow", "veryslow"]
_BITRATE_SHORTCUTS = [("2M", "2000k"), ("4M", "4000k"), ("8M", "8000k")]


class ParameterPanelWidget(QWidget):
    """Button-group based panel for configuring video compression parameters."""

    params_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("压缩参数")
        grid = QGridLayout(group)
        grid.setSpacing(8)
        row = 0

        # Quality preset
        grid.addWidget(QLabel("质量预设:"), row, 0)
        preset_options = ["自定义"] + list(QUALITY_PRESETS.keys())
        self._preset_group, self._preset_btns = self._make_btn_row(preset_options, "自定义")
        grid.addLayout(self._btn_layout(self._preset_btns), row, 1)
        row += 1

        # Resolution
        grid.addWidget(QLabel("分辨率:"), row, 0)
        res_options = ["不更改"] + list(RESOLUTION_PRESETS.keys())
        self._resolution_group, self._resolution_btns = self._make_btn_row(res_options, "不更改")
        grid.addLayout(self._btn_layout(self._resolution_btns), row, 1)
        row += 1

        # Video bitrate (shortcuts + line edit)
        grid.addWidget(QLabel("视频码率:"), row, 0)
        vb_row = QHBoxLayout()
        self._bitrate_shortcut_btns: list[QPushButton] = []
        for label, value in _BITRATE_SHORTCUTS:
            btn = QPushButton(label)
            btn.setStyleSheet(_SHORTCUT_BTN_STYLE)
            btn.clicked.connect(lambda checked, v=value: self._on_bitrate_shortcut(v))
            vb_row.addWidget(btn)
            self._bitrate_shortcut_btns.append(btn)
        self._video_bitrate = QLineEdit()
        self._video_bitrate.setPlaceholderText("例如: 4000k 或 5M")
        vb_row.addWidget(self._video_bitrate, stretch=1)
        grid.addLayout(vb_row, row, 1)
        row += 1

        # Audio bitrate
        grid.addWidget(QLabel("音频码率:"), row, 0)
        self._audio_group, self._audio_btns = self._make_btn_row(_AUDIO_BITRATES, "不更改")
        grid.addLayout(self._btn_layout(self._audio_btns), row, 1)
        row += 1

        # Framerate
        grid.addWidget(QLabel("帧率:"), row, 0)
        self._framerate_group, self._framerate_btns = self._make_btn_row(_FRAMERATES, "不更改")
        grid.addLayout(self._btn_layout(self._framerate_btns), row, 1)
        row += 1

        # Encoding preset (2 rows of 3)
        grid.addWidget(QLabel("编码预设:"), row, 0)
        enc_layout = QGridLayout()
        enc_layout.setSpacing(6)
        self._encoding_group = QButtonGroup(self)
        self._encoding_group.setExclusive(True)
        self._encoding_btns: list[QPushButton] = []
        for i, preset in enumerate(_ENCODING_PRESETS):
            btn = QPushButton(preset)
            btn.setCheckable(True)
            btn.setStyleSheet(_BTN_STYLE)
            if preset == "medium":
                btn.setChecked(True)
            enc_layout.addWidget(btn, i // 3, i % 3)
            self._encoding_group.addButton(btn, i)
            self._encoding_btns.append(btn)
        grid.addLayout(enc_layout, row, 1)
        row += 1

        outer.addWidget(group)

        # Connect signals
        self._preset_group.idClicked.connect(self._on_preset_changed)
        self._resolution_group.idClicked.connect(lambda _: self.params_changed.emit())
        self._video_bitrate.textChanged.connect(lambda _: self.params_changed.emit())
        self._audio_group.idClicked.connect(lambda _: self.params_changed.emit())
        self._framerate_group.idClicked.connect(lambda _: self.params_changed.emit())
        self._encoding_group.idClicked.connect(lambda _: self.params_changed.emit())

    # -- Helpers ---------------------------------------------------------------

    def _make_btn_row(
        self, options: list[str], default: str
    ) -> tuple[QButtonGroup, list[QPushButton]]:
        group = QButtonGroup(self)
        group.setExclusive(True)
        btns: list[QPushButton] = []
        for i, text in enumerate(options):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet(_BTN_STYLE)
            if text == default:
                btn.setChecked(True)
            group.addButton(btn, i)
            btns.append(btn)
        return group, btns

    @staticmethod
    def _btn_layout(btns: list[QPushButton]) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(6)
        for btn in btns:
            row.addWidget(btn)
        row.addStretch()
        return row

    def _on_bitrate_shortcut(self, value: str) -> None:
        self._video_bitrate.setText(value)

    def _on_preset_changed(self, btn_id: int) -> None:
        text = self._preset_btns[btn_id].text()
        if text in QUALITY_PRESETS:
            params = QUALITY_PRESETS[text]
            # Video bitrate
            self._video_bitrate.setText(params.video_bitrate or "")
            # Audio bitrate
            if params.audio_bitrate and params.audio_bitrate in _AUDIO_BITRATES:
                idx = _AUDIO_BITRATES.index(params.audio_bitrate)
                self._audio_btns[idx].setChecked(True)
            # Encoding preset
            if params.preset in _ENCODING_PRESETS:
                idx = _ENCODING_PRESETS.index(params.preset)
                self._encoding_btns[idx].setChecked(True)
        self.params_changed.emit()

    def get_params(self) -> CompressionParams:
        """Return the currently configured compression parameters."""
        # Resolution
        resolution = None
        res_id = self._resolution_group.checkedId()
        if res_id > 0:
            res_keys = list(RESOLUTION_PRESETS.keys())
            resolution = RESOLUTION_PRESETS[res_keys[res_id - 1]]

        # Video bitrate
        video_bitrate = self._video_bitrate.text().strip() or None

        # Audio bitrate
        audio_bitrate = None
        ab_id = self._audio_group.checkedId()
        if ab_id > 0:
            audio_bitrate = _AUDIO_BITRATES[ab_id]

        # Framerate
        framerate = None
        fr_id = self._framerate_group.checkedId()
        if fr_id > 0:
            framerate = float(_FRAMERATES[fr_id])

        # Encoding preset
        enc_id = self._encoding_group.checkedId()
        preset = _ENCODING_PRESETS[enc_id] if enc_id >= 0 else "medium"

        return CompressionParams(
            resolution=resolution,
            video_bitrate=video_bitrate,
            audio_bitrate=audio_bitrate,
            framerate=framerate,
            preset=preset,
        )
