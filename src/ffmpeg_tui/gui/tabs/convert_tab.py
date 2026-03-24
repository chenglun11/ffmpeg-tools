"""Format conversion tab."""

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
from ..widgets.format_selector import FormatSelectorWidget
from ..widgets.progress_panel import ProgressPanelWidget
from ..worker import FFmpegWorker


class ConvertTab(QWidget):
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

        # Format selector
        self._format_selector = FormatSelectorWidget("输出格式:")
        layout.addWidget(self._format_selector)

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

        layout.addStretch()

        # Connections
        self._file_picker.file_selected.connect(self._on_file_selected)
        self._format_selector.format_changed.connect(self._on_format_changed)
        self._start_btn.clicked.connect(self._start_convert)
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

        info_parts = [
            path.name,
            format_file_size(size),
        ]
        if self._duration > 0:
            info_parts.append(format_duration(self._duration))
        self._file_info_label.setText("  |  ".join(info_parts))
        self._file_info_label.setStyleSheet("")

        # Auto-generate output path
        ext, _, _ = self._format_selector.selected_format()
        if ext:
            self._output_edit.setText(str(generate_output_path(path, ext)))

    def _on_format_changed(self, ext: str, video_codec, audio_codec) -> None:
        if self._input_path and ext:
            self._output_edit.setText(str(generate_output_path(self._input_path, ext)))

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

        ext, video_codec, audio_codec = self._format_selector.selected_format()

        builder = CommandBuilder(str(ffmpeg_path))
        command = builder.build_convert_command(
            self._input_path,
            output_path,
            video_codec=video_codec,
            audio_codec=audio_codec,
        )

        self._start_btn.setEnabled(False)
        self._progress.reset()

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
            if output.exists():
                size_str = format_file_size(output.stat().st_size)
                self._progress.set_completed(True, f"转换完成! 输出: {size_str}")
            else:
                self._progress.set_completed(True)
        else:
            self._progress.set_completed(False, "转换失败")

    def _on_error(self, msg: str) -> None:
        self._start_btn.setEnabled(True)
        self._progress.set_completed(False, f"错误: {msg}")
