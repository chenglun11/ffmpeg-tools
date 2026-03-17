"""Meta (WhatsApp) media conversion tab."""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ffmpeg_tui.core.ffmpeg_executor import FFmpegExecutor
from ffmpeg_tui.core.ffmpeg_manager import FFmpegManager
from ffmpeg_tui.utils.file_utils import (
    format_duration,
    format_file_size,
    generate_output_path,
    validate_input_file,
)

from ..widgets.file_picker import FilePickerWidget
from ..widgets.progress_panel import ProgressPanelWidget
from ..worker import FFmpegWorker

_BTN_STYLE = """
    QPushButton {
        background-color: #f3f4f6;
        color: #374151;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 8px 14px;
        font-size: 12px;
        font-weight: bold;
        min-width: 60px;
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
# ── Presets ──────────────────────────────────────────────────────────────────

_MAX_VIDEO_SIZE = 16 * 1024 * 1024   # 16 MB
_MAX_AUDIO_SIZE = 16 * 1024 * 1024   # 16 MB
_MAX_IMAGE_SIZE = 5 * 1024 * 1024    # 5 MB

_MEDIA_TYPES = {
    "视频 (MP4)": {
        "type": "video",
        "ext": "mp4",
        "desc": "MP4  |  H.264 Main  |  AAC  |  ≤16MB",
        "max_size": _MAX_VIDEO_SIZE,
        "suffix": "_wa",
    },
    "音频 (AAC)": {
        "type": "audio",
        "ext": "aac",
        "desc": "AAC 音频  |  ≤16MB",
        "max_size": _MAX_AUDIO_SIZE,
        "suffix": "_wa",
    },
    "音频 (MP3)": {
        "type": "audio",
        "ext": "mp3",
        "desc": "MP3 音频  |  ≤16MB",
        "max_size": _MAX_AUDIO_SIZE,
        "suffix": "_wa",
    },
    "音频 (OGG)": {
        "type": "audio",
        "ext": "ogg",
        "desc": "OGG Opus 单声道  |  ≤16MB",
        "max_size": _MAX_AUDIO_SIZE,
        "suffix": "_wa",
    },
    "图片 (JPEG)": {
        "type": "image",
        "ext": "jpg",
        "desc": "JPEG  |  8-bit RGB  |  ≤5MB",
        "max_size": _MAX_IMAGE_SIZE,
        "suffix": "_wa",
    },
    "图片 (PNG)": {
        "type": "image",
        "ext": "png",
        "desc": "PNG  |  8-bit RGB/RGBA  |  ≤5MB",
        "max_size": _MAX_IMAGE_SIZE,
        "suffix": "_wa",
    },
}


class MetaTab(QWidget):
    def __init__(self, manager: FFmpegManager, parent=None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._worker: Optional[FFmpegWorker] = None
        self._input_path: Optional[Path] = None
        self._duration: float = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # File picker
        self._file_picker = FilePickerWidget("输入文件:")
        layout.addWidget(self._file_picker)

        # File info
        self._file_info_label = QLabel()
        layout.addWidget(self._file_info_label)

        # Media type selector
        type_group = QGroupBox("目标格式")
        type_layout = QVBoxLayout(type_group)
        type_layout.setSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self._type_group = QButtonGroup(self)
        self._type_group.setExclusive(True)
        self._type_btns: list[QPushButton] = []
        self._type_keys = list(_MEDIA_TYPES.keys())

        for i, key in enumerate(self._type_keys):
            btn = QPushButton(key)
            btn.setCheckable(True)
            btn.setStyleSheet(_BTN_STYLE)
            self._type_group.addButton(btn, i)
            self._type_btns.append(btn)
            btn_row.addWidget(btn)
        btn_row.addStretch()
        type_layout.addLayout(btn_row)

        self._type_desc = QLabel()
        self._type_desc.setStyleSheet("color: #6b7280; font-size: 12px;")
        type_layout.addWidget(self._type_desc)

        layout.addWidget(type_group)

        # Default to video
        self._type_btns[0].setChecked(True)
        self._update_desc(0)

        # Spec info
        spec_group = QGroupBox("输出规格")
        spec_layout = QVBoxLayout(spec_group)
        self._spec_label = QLabel()
        self._spec_label.setWordWrap(True)
        self._spec_label.setStyleSheet("color: #374151; font-size: 12px;")
        spec_layout.addWidget(self._spec_label)
        layout.addWidget(spec_group)
        self._update_spec(0)

        # Output path
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("输出路径:"))
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("自动生成，或手动指定…")
        out_row.addWidget(self._output_edit, stretch=1)
        layout.addLayout(out_row)

        # Start button
        self._start_btn = QPushButton("开始转换")
        self._start_btn.setObjectName("primaryBtn")
        self._start_btn.setMinimumHeight(40)
        layout.addWidget(self._start_btn)

        # Progress
        self._progress = ProgressPanelWidget()
        layout.addWidget(self._progress)

        # Result
        self._result_label = QLabel()
        layout.addWidget(self._result_label)

        layout.addStretch()

        # Connections
        self._file_picker.file_selected.connect(self._on_file_selected)
        self._type_group.idClicked.connect(self._on_type_changed)
        self._start_btn.clicked.connect(self._start_convert)
        self._progress.cancel_clicked.connect(self._cancel)
# ── Methods ──────────────────────────────────────────────────────────────────

    def _current_type(self) -> dict:
        idx = self._type_group.checkedId()
        if idx < 0:
            idx = 0
        return _MEDIA_TYPES[self._type_keys[idx]]

    def _update_desc(self, idx: int) -> None:
        t = _MEDIA_TYPES[self._type_keys[idx]]
        self._type_desc.setText(t["desc"])

    def _update_spec(self, idx: int) -> None:
        t = _MEDIA_TYPES[self._type_keys[idx]]
        max_mb = t["max_size"] / (1024 * 1024)
        if t["type"] == "video":
            lines = [
                "编码: H.264 Main profile (无 B-frames) + AAC",
                "容器: MP4 (moov 前置 faststart)",
                "色彩: yuv420p",
                f"文件上限: {max_mb:.0f} MB",
                "提示: 自动根据时长计算码率以控制文件大小",
            ]
        elif t["type"] == "audio":
            codec_map = {"aac": "AAC", "mp3": "MP3 (LAME)", "ogg": "Opus 单声道"}
            codec = codec_map.get(t["ext"], t["ext"])
            lines = [
                f"编码: {codec}",
                f"文件上限: {max_mb:.0f} MB",
            ]
        else:
            lines = [
                f"格式: {t['ext'].upper()}  |  8-bit RGB",
                f"文件上限: {max_mb:.0f} MB",
            ]
        self._spec_label.setText("\n".join(lines))

    def _on_type_changed(self, idx: int) -> None:
        self._update_desc(idx)
        self._update_spec(idx)
        if self._input_path:
            t = _MEDIA_TYPES[self._type_keys[idx]]
            self._output_edit.setText(
                str(generate_output_path(self._input_path, t["ext"], t["suffix"]))
            )

    def _on_file_selected(self, path: Path) -> None:
        valid, msg = validate_input_file(path)
        if not valid:
            self._file_info_label.setText(msg)
            self._file_info_label.setStyleSheet("color: red;")
            self._input_path = None
            return

        self._input_path = path
        size = path.stat().st_size

        ffprobe = self._manager.get_ffprobe_path()
        probe_str = str(ffprobe) if ffprobe else "ffprobe"
        self._duration = FFmpegExecutor.get_duration(path, probe_str)

        info_parts = [path.name, format_file_size(size)]
        if self._duration > 0:
            info_parts.append(format_duration(self._duration))
        self._file_info_label.setText("  |  ".join(info_parts))
        self._file_info_label.setStyleSheet("")

        t = self._current_type()
        self._output_edit.setText(
            str(generate_output_path(path, t["ext"], t["suffix"]))
        )

    def _calc_video_bitrate(self, duration: float, max_bytes: int) -> str:
        """Calculate video bitrate to fit within max_bytes.

        Reserve 10% for audio + container overhead.
        """
        if duration <= 0:
            return "2000k"
        usable_bytes = max_bytes * 0.88  # reserve for audio + overhead
        bitrate_kbps = int((usable_bytes * 8) / duration / 1000)
        # Clamp: min 500k, max 8000k
        bitrate_kbps = max(500, min(bitrate_kbps, 8000))
        return f"{bitrate_kbps}k"

    def _build_command(self) -> list[str]:
        ffmpeg_path = str(self._manager.get_ffmpeg_path())
        t = self._current_type()
        output = self._output_edit.text().strip()

        if t["type"] == "video":
            target_bitrate = self._calc_video_bitrate(self._duration, t["max_size"])
            return [
                ffmpeg_path,
                "-i", str(self._input_path),
                "-c:v", "libx264",
                "-profile:v", "main",
                "-level", "3.1",
                "-preset", "medium",
                "-crf", "23",
                "-maxrate", target_bitrate,
                "-bufsize", str(int(target_bitrate.rstrip("k")) * 2) + "k",
                "-r", "30",
                "-c:a", "aac",
                "-b:a", "128k",
                "-ar", "44100",
                "-movflags", "+faststart",
                "-pix_fmt", "yuv420p",
                "-y", "-progress", "pipe:1",
                output,
            ]
        elif t["type"] == "audio":
            ext = t["ext"]
            if ext == "aac":
                return [
                    ffmpeg_path,
                    "-i", str(self._input_path),
                    "-vn",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-ar", "44100",
                    "-y", "-progress", "pipe:1",
                    output,
                ]
            elif ext == "mp3":
                return [
                    ffmpeg_path,
                    "-i", str(self._input_path),
                    "-vn",
                    "-c:a", "libmp3lame",
                    "-b:a", "128k",
                    "-ar", "44100",
                    "-y", "-progress", "pipe:1",
                    output,
                ]
            else:  # ogg opus mono
                return [
                    ffmpeg_path,
                    "-i", str(self._input_path),
                    "-vn",
                    "-c:a", "libopus",
                    "-b:a", "128k",
                    "-ac", "1",
                    "-ar", "48000",
                    "-y", "-progress", "pipe:1",
                    output,
                ]
        else:  # image
            ext = t["ext"]
            if ext == "jpg":
                return [
                    ffmpeg_path,
                    "-i", str(self._input_path),
                    "-vframes", "1",
                    "-pix_fmt", "rgb24",
                    "-q:v", "2",
                    "-y", "-progress", "pipe:1",
                    output,
                ]
            else:  # png
                return [
                    ffmpeg_path,
                    "-i", str(self._input_path),
                    "-vframes", "1",
                    "-pix_fmt", "rgba",
                    "-y", "-progress", "pipe:1",
                    output,
                ]

    def _start_convert(self) -> None:
        if not self._input_path:
            QMessageBox.warning(self, "提示", "请先选择输入文件")
            return

        output_text = self._output_edit.text().strip()
        if not output_text:
            QMessageBox.warning(self, "提示", "请指定输出路径")
            return

        output_path = Path(output_text)
        if output_path.exists():
            reply = QMessageBox.question(
                self, "确认覆盖",
                f"输出文件已存在:\n{output_path.name}\n\n是否覆盖？",
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        ffmpeg_path = self._manager.get_ffmpeg_path()
        if not ffmpeg_path:
            QMessageBox.critical(self, "错误", "未找到 FFmpeg，请在设置中安装")
            return

        self._start_btn.setEnabled(False)
        self._result_label.setText("")
        self._progress.reset()

        command = self._build_command()
        self._worker = FFmpegWorker(command, self._duration)
        self._worker.progress.connect(self._progress.update_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _cancel(self) -> None:
        if self._worker:
            self._worker.cancel()

    def _on_finished(self, success: bool) -> None:
        self._start_btn.setEnabled(True)
        if not success and self._worker and self._worker._executor._cancelled:
            self._progress.set_cancelled()
            return
        if success:
            output = Path(self._output_edit.text())
            t = self._current_type()
            if output.exists():
                out_size = output.stat().st_size
                size_str = format_file_size(out_size)
                if out_size > t["max_size"]:
                    max_mb = t["max_size"] / (1024 * 1024)
                    self._progress.set_completed(True, "转换完成!")
                    self._result_label.setText(
                        f"输出: {size_str}  |  "
                        f"超出 {max_mb:.0f}MB 限制，可能无法上传"
                    )
                    self._result_label.setStyleSheet("color: orange; font-weight: bold;")
                else:
                    self._progress.set_completed(True, "转换完成!")
                    orig_str = ""
                    if self._input_path:
                        orig_str = f"原始: {format_file_size(self._input_path.stat().st_size)}  →  "
                    self._result_label.setText(f"{orig_str}输出: {size_str}")
                    self._result_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self._progress.set_completed(True)
        else:
            self._progress.set_completed(False, "转换失败")

    def _on_error(self, msg: str) -> None:
        self._start_btn.setEnabled(True)
        self._progress.set_completed(False, f"错误: {msg}")
