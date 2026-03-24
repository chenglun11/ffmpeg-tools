"""Format selector widget: container + video codec + audio codec combo boxes."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ffmpeg_tui.models.format_config import (
    AUDIO_CODECS,
    CONTAINERS,
    VIDEO_CODECS,
    ContainerInfo,
)

_COMBO_STYLE = """
    QComboBox {
        background-color: #f3f4f6;
        color: #374151;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 13px;
        min-height: 28px;
    }
    QComboBox:hover {
        border-color: #a78bfa;
    }
    QComboBox:focus {
        border-color: #7c3aed;
    }
    QComboBox::drop-down {
        border: none;
        width: 24px;
    }
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #6b7280;
        margin-right: 6px;
    }
"""

_LABEL_STYLE = "font-size: 12px; font-weight: bold; color: #4b5563;"
_DESC_STYLE = "color: #6b7280; font-size: 12px;"


class FormatSelectorWidget(QWidget):
    """Container + codec selector. Emits *format_changed* with (extension, video_codec, audio_codec)."""

    format_changed = pyqtSignal(str, object, object)  # (ext, video_codec|None, audio_codec|None)

    def __init__(self, label: str = "输出格式:", parent=None) -> None:
        super().__init__(parent)
        self._updating = False  # guard against recursive signals

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # -- Container row --
        container_group = QGroupBox("容器格式")
        container_layout = QVBoxLayout(container_group)
        container_layout.setSpacing(4)

        self._container_combo = QComboBox()
        self._container_combo.setStyleSheet(_COMBO_STYLE)
        container_layout.addWidget(self._container_combo)

        self._container_desc = QLabel()
        self._container_desc.setStyleSheet(_DESC_STYLE)
        container_layout.addWidget(self._container_desc)

        layout.addWidget(container_group)

        # -- Codec row (side by side) --
        codec_group = QGroupBox("编码器")
        codec_grid = QGridLayout(codec_group)
        codec_grid.setSpacing(6)

        codec_grid.addWidget(self._make_label("视频编码:"), 0, 0)
        self._video_codec_combo = QComboBox()
        self._video_codec_combo.setStyleSheet(_COMBO_STYLE)
        codec_grid.addWidget(self._video_codec_combo, 0, 1)

        codec_grid.addWidget(self._make_label("音频编码:"), 1, 0)
        self._audio_codec_combo = QComboBox()
        self._audio_codec_combo.setStyleSheet(_COMBO_STYLE)
        codec_grid.addWidget(self._audio_codec_combo, 1, 1)

        codec_grid.setColumnStretch(1, 1)
        layout.addWidget(codec_group)

        # -- Populate containers --
        self._populate_containers()

        # -- Connections --
        self._container_combo.currentIndexChanged.connect(self._on_container_changed)
        self._video_codec_combo.currentIndexChanged.connect(self._on_codec_changed)
        self._audio_codec_combo.currentIndexChanged.connect(self._on_codec_changed)

        # Select first item to trigger initial population
        if self._container_combo.count() > 0:
            self._on_container_changed(0)

    # ----- helpers --------------------------------------------------------

    @staticmethod
    def _make_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(_LABEL_STYLE)
        return lbl

    # ----- populate -------------------------------------------------------

    def _populate_containers(self) -> None:
        self._container_combo.blockSignals(True)

        # Video containers first
        self._container_combo.addItem("── 视频容器 ──", None)
        idx = self._container_combo.count() - 1
        model = self._container_combo.model()
        item = model.item(idx)
        item.setEnabled(False)

        for key, info in CONTAINERS.items():
            if not info.is_audio_only:
                self._container_combo.addItem(f"{info.name}  ({info.extension})", key)

        # Separator: audio containers
        self._container_combo.addItem("── 音频容器 ──", None)
        idx = self._container_combo.count() - 1
        item = model.item(idx)
        item.setEnabled(False)

        for key, info in CONTAINERS.items():
            if info.is_audio_only:
                self._container_combo.addItem(f"{info.name}  ({info.extension})", key)

        self._container_combo.blockSignals(False)
        # Select first real item (index 1, skipping the header)
        self._container_combo.setCurrentIndex(1)

    def _update_codec_combos(self, container: ContainerInfo) -> None:
        self._updating = True

        # Video codecs
        self._video_codec_combo.blockSignals(True)
        self._video_codec_combo.clear()
        if container.is_audio_only:
            self._video_codec_combo.addItem("(纯音频，无视频)", None)
            self._video_codec_combo.setEnabled(False)
        else:
            self._video_codec_combo.setEnabled(True)
            default_idx = 0
            for i, codec_name in enumerate(container.compatible_video_codecs):
                codec = VIDEO_CODECS.get(codec_name)
                if codec:
                    self._video_codec_combo.addItem(
                        f"{codec.display_name}  ({codec.codec_name})", codec_name
                    )
                    if codec_name == container.default_video_codec:
                        default_idx = i
            self._video_codec_combo.setCurrentIndex(default_idx)
        self._video_codec_combo.blockSignals(False)

        # Audio codecs
        self._audio_codec_combo.blockSignals(True)
        self._audio_codec_combo.clear()
        default_idx = 0
        for i, codec_name in enumerate(container.compatible_audio_codecs):
            codec = AUDIO_CODECS.get(codec_name)
            if codec:
                self._audio_codec_combo.addItem(
                    f"{codec.display_name}  ({codec.codec_name})", codec_name
                )
                if codec_name == container.default_audio_codec:
                    default_idx = i
        self._audio_codec_combo.setCurrentIndex(default_idx)
        self._audio_codec_combo.blockSignals(False)

        self._updating = False

    # ----- slots ----------------------------------------------------------

    def _on_container_changed(self, index: int) -> None:
        key = self._container_combo.currentData()
        if key is None:
            return
        info = CONTAINERS.get(key)
        if not info:
            return
        self._container_desc.setText(info.description)
        self._update_codec_combos(info)
        self._emit_change()

    def _on_codec_changed(self, _index: int) -> None:
        if not self._updating:
            self._emit_change()

    def _emit_change(self) -> None:
        ext, vcodec, acodec = self.selected_format()
        self.format_changed.emit(ext, vcodec, acodec)

    # ----- public API -----------------------------------------------------

    def selected_format(self) -> tuple[str, str | None, str | None]:
        """Return (extension, video_codec_or_None, audio_codec_or_None)."""
        key = self._container_combo.currentData()
        if not key:
            return ("mp4", "libx264", "aac")  # fallback

        info = CONTAINERS[key]
        ext = info.extension

        video_codec = None
        if not info.is_audio_only:
            video_codec = self._video_codec_combo.currentData()

        audio_codec = self._audio_codec_combo.currentData()
        return (ext, video_codec, audio_codec)
