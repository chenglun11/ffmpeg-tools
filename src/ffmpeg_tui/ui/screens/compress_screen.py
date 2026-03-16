"""Compress screen for video compression with parameter configuration."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from ffmpeg_tui.core.command_builder import CommandBuilder
from ffmpeg_tui.core.ffmpeg_executor import FFmpegExecutor
from ffmpeg_tui.core.progress_parser import ProgressInfo
from ffmpeg_tui.models.conversion_task import CompressionParams
from ffmpeg_tui.ui.widgets.file_picker import FilePicker
from ffmpeg_tui.ui.widgets.parameter_panel import ParameterPanel
from ffmpeg_tui.ui.widgets.progress_display import ProgressDisplay
from ffmpeg_tui.utils.file_utils import (
    format_file_size,
    generate_output_path,
    validate_input_file,
)


class CompressScreen(Screen):
    """Video compression screen with parameter panel and progress display."""

    BINDINGS = [
        ("escape", "go_back", "返回"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._executor = FFmpegExecutor()
        self._builder = CommandBuilder()
        self._input_path: Path | None = None
        self._output_path: Path | None = None
        self._is_running = False
        self._current_params = CompressionParams()
        self._duration = 0.0

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="compress-container"):
            yield Static("视频压缩 (Video Compress)", classes="title")

            # Input file selection
            with Vertical(id="file-section"):
                yield Static("文件选择", classes="subtitle")
                yield Label("输入文件:")
                yield FilePicker(placeholder="选择要压缩的视频文件...", id="input-picker")
                yield Static("", id="input-file-info")

                yield Label("输出文件:")
                yield Input(
                    placeholder="输出文件路径（留空自动生成）",
                    id="output-file-path",
                )

            # Parameter panel
            yield ParameterPanel(id="parameter-panel")

            # Estimated output size
            yield Static("", id="estimate-info")

            # Action buttons
            with Horizontal(id="compress-buttons"):
                yield Button("开始压缩", id="btn-start", variant="success")
                yield Button("返回主菜单", id="btn-back", variant="default")

            # Progress display (hidden by default)
            yield ProgressDisplay(id="compress-progress")

            # Result area
            yield Static("", id="result-info")

        yield Footer()

    def on_file_picker_file_selected(self, event: FilePicker.FileSelected) -> None:
        """Handle file selection from the FilePicker widget."""
        path = event.path
        info_widget = self.query_one("#input-file-info", Static)

        valid, error = validate_input_file(path)
        if not valid:
            info_widget.update(f"[red]{error}[/red]")
            self._input_path = None
            return

        self._input_path = path
        size = format_file_size(path.stat().st_size)
        self._duration = FFmpegExecutor.get_duration(path)
        if self._duration > 0:
            mins = int(self._duration // 60)
            secs = int(self._duration % 60)
            info_widget.update(
                f"[green]文件有效[/green]  |  大小: {size}  |  时长: {mins:02d}:{secs:02d}"
            )
        else:
            info_widget.update(f"[green]文件有效[/green]  |  大小: {size}")

        # Auto-generate output path if empty
        output_input = self.query_one("#output-file-path", Input)
        if not output_input.value.strip():
            auto_output = generate_output_path(path, path.suffix.lstrip("."), suffix="_compressed")
            output_input.value = str(auto_output)

        self._update_estimate()

    def on_parameter_panel_params_changed(self, event: ParameterPanel.ParamsChanged) -> None:
        """Handle parameter changes from the panel."""
        self._current_params = event.params
        self._update_estimate()

    def _update_estimate(self) -> None:
        """Update estimated output file size based on current parameters."""
        estimate_widget = self.query_one("#estimate-info", Static)
        if not self._input_path or not self._input_path.exists():
            estimate_widget.update("")
            return

        input_size = self._input_path.stat().st_size
        if self._duration <= 0:
            estimate_widget.update("")
            return

        params = self._current_params
        if params.video_bitrate:
            br_str = params.video_bitrate.lower()
            try:
                if br_str.endswith("m"):
                    bits_per_sec = float(br_str[:-1]) * 1_000_000
                elif br_str.endswith("k"):
                    bits_per_sec = float(br_str[:-1]) * 1_000
                else:
                    bits_per_sec = float(br_str)
                estimated_bytes = int((bits_per_sec / 8) * self._duration * 1.1)
                ratio = estimated_bytes / input_size if input_size > 0 else 0
                estimate_widget.update(
                    f"预估输出大小: ~{format_file_size(estimated_bytes)}  |  "
                    f"压缩比: ~{ratio:.1%}"
                )
                return
            except ValueError:
                pass

        estimate_widget.update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            if self._is_running:
                self.notify("请先取消正在执行的压缩任务", title="提示", severity="warning")
                return
            self.app.pop_screen()
        elif event.button.id == "btn-start":
            self._start_compress()

    def on_progress_display_cancel_requested(
        self, event: ProgressDisplay.CancelRequested,
    ) -> None:
        """Handle cancel from ProgressDisplay widget."""
        self._cancel_compress()

    def _start_compress(self) -> None:
        """Validate inputs and start the compression task."""
        if self._is_running:
            return

        if not self._input_path:
            self.notify("请先选择输入文件", title="错误", severity="error")
            return
        valid, error = validate_input_file(self._input_path)
        if not valid:
            self.notify(error, title="错误", severity="error")
            return

        # Determine output path
        output_str = self.query_one("#output-file-path", Input).value.strip()
        if output_str:
            self._output_path = Path(output_str).expanduser()
        else:
            self._output_path = generate_output_path(
                self._input_path, self._input_path.suffix.lstrip("."), suffix="_compressed"
            )

        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get params and build command
        params = self.query_one("#parameter-panel", ParameterPanel).get_params()
        command = self._builder.build_compress_command(
            input_file=self._input_path,
            output_file=self._output_path,
            resolution=params.resolution,
            video_bitrate=params.video_bitrate,
            audio_bitrate=params.audio_bitrate,
            framerate=params.framerate,
            preset=params.preset,
        )

        # Update UI state
        self._is_running = True
        self.query_one("#btn-start", Button).disabled = True
        self.query_one("#result-info", Static).update("")

        progress_display = self.query_one("#compress-progress", ProgressDisplay)
        progress_display.show()

        self.run_worker(self._run_compress(command, self._duration), exclusive=True)

    async def _run_compress(self, command: list[str], duration: float) -> None:
        """Run the compression in background."""
        input_size = self._input_path.stat().st_size if self._input_path else 0

        def on_progress(info: ProgressInfo) -> None:
            pct = info.percentage(duration)
            eta = 0.0
            if info.speed > 0 and duration > 0:
                remaining_time = duration - info.out_time_seconds
                eta = remaining_time / info.speed
            self.call_from_thread(
                self._update_progress, pct, info.frame, info.fps, info.speed, eta,
            )

        success = await self._executor.execute(
            command=command,
            total_duration=duration,
            progress_callback=on_progress,
        )

        self.call_from_thread(self._on_compress_finished, success, input_size)

    def _update_progress(
        self,
        percentage: float,
        frame: int,
        fps: float,
        speed: float,
        eta: float,
    ) -> None:
        """Update the ProgressDisplay widget."""
        progress_display = self.query_one("#compress-progress", ProgressDisplay)
        progress_display.update_progress(
            percentage=percentage,
            frame=frame,
            fps=fps,
            speed=speed,
            eta_seconds=eta,
        )

    def _on_compress_finished(self, success: bool, input_size: int) -> None:
        """Handle compression completion."""
        self._is_running = False
        self.query_one("#btn-start", Button).disabled = False
        progress_display = self.query_one("#compress-progress", ProgressDisplay)

        if success:
            result_parts = ["[green]压缩成功![/green]"]
            if self._output_path and self._output_path.exists():
                output_size = self._output_path.stat().st_size
                result_parts.append(f"输出文件: {self._output_path}")
                result_parts.append(
                    f"原始大小: {format_file_size(input_size)}  ->  "
                    f"压缩后: {format_file_size(output_size)}"
                )
                if input_size > 0:
                    ratio = output_size / input_size
                    saved = 1.0 - ratio
                    result_parts.append(f"压缩比: {ratio:.1%}  |  节省: {saved:.1%}")
                msg = "\n".join(result_parts)
            else:
                msg = ""
            progress_display.set_completed(success=True, message=msg)
            self.query_one("#result-info", Static).update("\n".join(result_parts))
            self.notify("视频压缩完成!", title="成功")
        else:
            if self._executor._cancelled:
                progress_display.set_cancelled()
                self.query_one("#result-info", Static).update("[yellow]压缩已取消[/yellow]")
            else:
                progress_display.set_completed(
                    success=False,
                    message="[red]压缩失败，请检查输入文件和参数设置。[/red]",
                )
                self.query_one("#result-info", Static).update(
                    "[red]压缩失败，请检查输入文件和参数设置。[/red]"
                )
                self.notify("压缩失败", title="错误", severity="error")

    def _cancel_compress(self) -> None:
        """Cancel the running compression."""
        if self._is_running:
            self._executor.cancel()

    def action_go_back(self) -> None:
        """Return to the main menu."""
        if self._is_running:
            self.notify("请先取消正在执行的压缩任务", title="提示", severity="warning")
            return
        self.app.pop_screen()
