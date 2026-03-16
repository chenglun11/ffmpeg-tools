"""Video compression tab."""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ffmpeg_tui.core.command_builder import CommandBuilder
from ffmpeg_tui.core.ffmpeg_executor import FFmpegExecutor
from ffmpeg_tui.core.ffmpeg_manager import FFmpegManager
from ffmpeg_tui.utils.file_utils import (
    format_duration,
    format_file_size,
    generate_output_path,
    validate_input_file,
)

from ..widgets.file_picker import FilePickerWidget
from ..widgets.parameter_panel import ParameterPanelWidget
from ..widgets.progress_panel import ProgressPanelWidget
from ..worker import FFmpegWorker


class CompressTab(QWidget):
    def __init__(self, manager: FFmpegManager, parent=None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._worker: Optional[FFmpegWorker] = None
        self._input_path: Optional[Path] = None
        self._duration: float = 0.0

        layout = QVBoxLayout(self)

        # File picker
        self._file_picker = FilePickerWidget("输入文件:")
        layout.addWidget(self._file_picker)

        # File info
        self._file_info_label = QLabel()
        layout.addWidget(self._file_info_label)

        # Parameters
        self._param_panel = ParameterPanelWidget()
        layout.addWidget(self._param_panel)

        # Estimated size
        self._estimate_label = QLabel()
        layout.addWidget(self._estimate_label)

        # Output path
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("输出路径:"))
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("自动生成，或手动指定…")
        out_row.addWidget(self._output_edit, stretch=1)
        layout.addLayout(out_row)

        # Start button
        self._start_btn = QPushButton("开始压缩")
        self._start_btn.setMinimumHeight(36)
        layout.addWidget(self._start_btn)

        # Progress
        self._progress = ProgressPanelWidget()
        layout.addWidget(self._progress)

        # Result summary
        self._result_label = QLabel()
        layout.addWidget(self._result_label)

        layout.addStretch()

        # Connections
        self._file_picker.file_selected.connect(self._on_file_selected)
        self._param_panel.params_changed.connect(self._update_estimate)
        self._start_btn.clicked.connect(self._start_compress)
        self._progress.cancel_clicked.connect(self._cancel)

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

        # Auto output path
        self._output_edit.setText(str(generate_output_path(path, path.suffix, "_compressed")))
        self._update_estimate()

    def _update_estimate(self) -> None:
        if not self._input_path or self._duration <= 0:
            self._estimate_label.setText("")
            return

        params = self._param_panel.get_params()
        if params.video_bitrate:
            br_text = params.video_bitrate.lower()
            if br_text.endswith("m"):
                bitrate_kbps = float(br_text[:-1]) * 1000
            elif br_text.endswith("k"):
                bitrate_kbps = float(br_text[:-1])
            else:
                try:
                    bitrate_kbps = float(br_text) / 1000
                except ValueError:
                    self._estimate_label.setText("")
                    return

            estimated_bytes = (bitrate_kbps * 1000 / 8) * self._duration
            self._estimate_label.setText(f"预估输出大小: {format_file_size(int(estimated_bytes))}")
        else:
            self._estimate_label.setText("")

    def _start_compress(self) -> None:
        if not self._input_path:
            QMessageBox.warning(self, "提示", "请先选择输入文件")
            return

        output_text = self._output_edit.text().strip()
        if not output_text:
            QMessageBox.warning(self, "提示", "请指定输出路径")
            return

        ffmpeg_path = self._manager.get_ffmpeg_path()
        if not ffmpeg_path:
            QMessageBox.critical(self, "错误", "未找到 FFmpeg，请在设置中安装")
            return

        output_path = Path(output_text)
        params = self._param_panel.get_params()

        builder = CommandBuilder(str(ffmpeg_path))
        command = builder.build_compress_command(
            self._input_path,
            output_path,
            resolution=params.resolution,
            video_bitrate=params.video_bitrate,
            audio_bitrate=params.audio_bitrate,
            framerate=params.framerate,
            preset=params.preset,
        )

        self._start_btn.setEnabled(False)
        self._result_label.setText("")
        self._progress.reset()

        self._worker = FFmpegWorker(command, self._duration)
        self._worker.progress.connect(self._progress.update_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _cancel(self) -> None:
        if self._worker:
            self._worker.cancel()
            self._progress.set_cancelled()
            self._start_btn.setEnabled(True)

    def _on_finished(self, success: bool) -> None:
        self._start_btn.setEnabled(True)
        if success:
            output = Path(self._output_edit.text())
            if output.exists() and self._input_path:
                original = self._input_path.stat().st_size
                compressed = output.stat().st_size
                ratio = (1 - compressed / original) * 100 if original > 0 else 0
                self._progress.set_completed(True, "压缩完成!")
                self._result_label.setText(
                    f"原始: {format_file_size(original)}  →  "
                    f"压缩后: {format_file_size(compressed)}  "
                    f"(节省 {ratio:.1f}%)"
                )
                self._result_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self._progress.set_completed(True)
        else:
            self._progress.set_completed(False, "压缩失败")

    def _on_error(self, msg: str) -> None:
        self._start_btn.setEnabled(True)
        self._progress.set_completed(False, f"错误: {msg}")
