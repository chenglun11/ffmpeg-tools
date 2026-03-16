"""Format conversion screen for FFmpeg TUI Tools."""

from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from ffmpeg_tui.core.command_builder import CommandBuilder
from ffmpeg_tui.core.ffmpeg_executor import FFmpegExecutor
from ffmpeg_tui.core.ffmpeg_manager import FFmpegManager
from ffmpeg_tui.core.progress_parser import ProgressInfo
from ffmpeg_tui.ui.widgets.file_picker import FilePicker
from ffmpeg_tui.ui.widgets.format_selector import FormatSelector, get_format_info, is_audio_only
from ffmpeg_tui.ui.widgets.progress_display import ProgressDisplay
from ffmpeg_tui.utils.file_utils import (
    generate_output_path,
    validate_input_file,
    format_file_size,
    format_duration,
    get_media_duration,
)


class ConvertScreen(Screen):
    """Screen for format conversion."""

    BINDINGS = [
        ("escape", "go_back", "返回"),
    ]

    DEFAULT_CSS = """
    ConvertScreen #convert-container {
        width: 100%;
        height: 1fr;
        padding: 1 4;
        overflow-y: auto;
    }
    ConvertScreen #convert-form {
        width: 100%;
        max-width: 100;
        height: auto;
        padding: 1 2;
    }
    ConvertScreen .section-title {
        text-style: bold;
        color: $accent;
        padding: 1 0 0 0;
        width: 100%;
    }
    ConvertScreen .file-info {
        color: $text-muted;
        padding: 0 1;
        height: auto;
        width: 100%;
    }
    ConvertScreen .output-row {
        layout: horizontal;
        height: auto;
        width: 100%;
    }
    ConvertScreen .output-row Input {
        width: 1fr;
        margin: 0;
    }
    ConvertScreen .output-row Button {
        width: auto;
        min-width: 14;
        margin: 0 0 0 1;
    }
    ConvertScreen #action-buttons {
        layout: horizontal;
        height: auto;
        width: 100%;
        align: center middle;
        padding: 1 0;
    }
    ConvertScreen #action-buttons Button {
        width: auto;
        min-width: 20;
        margin: 0 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._manager = FFmpegManager()
        self._executor = FFmpegExecutor()
        self._selected_format: str | None = None
        self._input_path: Path | None = None
        self._total_duration: float = 0.0

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="convert-container"):
            yield Static("格式转换 (Format Convert)", classes="title")

            with Vertical(id="convert-form"):
                # Input file section
                yield Static("输入文件", classes="section-title")
                yield FilePicker(placeholder="选择或输入媒体文件路径...", id="input-picker")
                yield Static("", id="input-info", classes="file-info")

                # Output format section
                yield Static("输出格式", classes="section-title")
                yield FormatSelector(id="format-selector")

                # Output path section
                yield Static("输出路径", classes="section-title")
                with Horizontal(classes="output-row"):
                    yield Input(
                        placeholder="自动生成输出路径...",
                        id="output-path",
                    )
                    yield Button("自动", id="btn-auto-path", variant="default")

                # Action buttons
                with Horizontal(id="action-buttons"):
                    yield Button("开始转换", id="btn-start", variant="success", disabled=True)
                    yield Button("返回主菜单", id="btn-back", variant="default")

                # Progress display
                yield ProgressDisplay(id="progress-display")

        yield Footer()

    @on(FilePicker.FileSelected)
    def _on_file_selected(self, event: FilePicker.FileSelected) -> None:
        """Handle file selection from the file picker."""
        event.stop()
        path = event.path
        valid, error = validate_input_file(path)
        if not valid:
            self.query_one("#input-info", Static).update(f"[red]{error}[/red]")
            self._input_path = None
            self._update_start_button()
            return

        self._input_path = path

        # Show file info
        size = format_file_size(path.stat().st_size)
        ffprobe = self._manager.get_ffprobe_path()
        ffprobe_str = str(ffprobe) if ffprobe else "ffprobe"
        duration = get_media_duration(path, ffprobe_str)
        self._total_duration = duration
        dur_str = format_duration(duration) if duration > 0 else "未知"
        self.query_one("#input-info", Static).update(
            f"文件: {path.name}  |  大小: {size}  |  时长: {dur_str}"
        )

        # Auto-generate output path if format is selected
        self._auto_generate_output()
        self._update_start_button()

    @on(FormatSelector.FormatChanged)
    def _on_format_changed(self, event: FormatSelector.FormatChanged) -> None:
        """Handle format selection change."""
        event.stop()
        self._selected_format = event.format_value
        self._auto_generate_output()
        self._update_start_button()

    @on(Button.Pressed, "#btn-auto-path")
    def _on_auto_path(self) -> None:
        """Auto-generate the output path."""
        self._auto_generate_output()

    @on(Button.Pressed, "#btn-start")
    def _on_start(self) -> None:
        """Start the conversion."""
        if not self._can_start():
            return
        self._run_conversion()

    @on(Button.Pressed, "#btn-back")
    def _on_back(self) -> None:
        """Return to the main menu."""
        self.app.pop_screen()

    @on(ProgressDisplay.CancelRequested)
    def _on_cancel(self) -> None:
        """Cancel the ongoing conversion."""
        self._executor.cancel()
        self.query_one("#progress-display", ProgressDisplay).set_cancelled()
        self._set_form_enabled(True)

    def _auto_generate_output(self) -> None:
        """Auto-generate output path based on input file and selected format."""
        if self._input_path and self._selected_format:
            output = generate_output_path(self._input_path, self._selected_format)
            self.query_one("#output-path", Input).value = str(output)

    def _can_start(self) -> bool:
        """Check if conversion can start."""
        if not self._input_path:
            self.notify("请先选择输入文件", severity="warning", title="提示")
            return False
        if not self._selected_format:
            self.notify("请先选择输出格式", severity="warning", title="提示")
            return False
        output_val = self.query_one("#output-path", Input).value.strip()
        if not output_val:
            self.notify("请指定输出路径", severity="warning", title="提示")
            return False
        if not self._manager.check_installation():
            self.notify("FFmpeg 未安装，请先在设置中安装", severity="error", title="错误")
            return False
        return True

    def _update_start_button(self) -> None:
        """Enable or disable the start button based on form state."""
        can_start = bool(
            self._input_path
            and self._selected_format
            and self.query_one("#output-path", Input).value.strip()
        )
        self.query_one("#btn-start", Button).disabled = not can_start

    def _set_form_enabled(self, enabled: bool) -> None:
        """Enable or disable form controls during conversion."""
        self.query_one("#btn-start", Button).disabled = not enabled
        self.query_one("#btn-auto-path", Button).disabled = not enabled

    @work(thread=False)
    async def _run_conversion(self) -> None:
        """Run the FFmpeg conversion in a worker."""
        progress_display = self.query_one("#progress-display", ProgressDisplay)
        progress_display.show()
        self._set_form_enabled(False)

        input_path = self._input_path
        output_path = Path(self.query_one("#output-path", Input).value.strip())
        format_info = get_format_info(self._selected_format)

        ffmpeg_path = self._manager.get_ffmpeg_path()
        if not ffmpeg_path:
            progress_display.set_completed(False, "[red]FFmpeg 未找到[/red]")
            self._set_form_enabled(True)
            return

        builder = CommandBuilder(str(ffmpeg_path))

        # Determine codecs based on format
        video_codec = format_info.default_video_codec if format_info else None
        audio_codec = format_info.default_audio_codec if format_info else None

        # For audio-only formats, skip video codec
        if self._selected_format and is_audio_only(self._selected_format):
            video_codec = None

        command = builder.build_convert_command(
            input_file=input_path,
            output_file=output_path,
            video_codec=video_codec,
            audio_codec=audio_codec,
        )

        total_duration = self._total_duration

        def on_progress(info: ProgressInfo) -> None:
            pct = info.percentage(total_duration)
            eta = 0.0
            if info.speed > 0 and total_duration > 0:
                remaining_time = total_duration - info.out_time_seconds
                eta = remaining_time / info.speed
            self.call_from_thread(
                progress_display.update_progress,
                percentage=pct,
                frame=info.frame,
                fps=info.fps,
                speed=info.speed,
                eta_seconds=eta,
            )

        success = await self._executor.execute(
            command=command,
            total_duration=total_duration,
            progress_callback=on_progress,
        )

        if success:
            out_size = ""
            if output_path.exists():
                out_size = f"  |  输出大小: {format_file_size(output_path.stat().st_size)}"
            progress_display.set_completed(
                True, f"[green]转换成功![/green]{out_size}\n输出: {output_path}"
            )
        elif not self._executor._cancelled:
            progress_display.set_completed(False)

        self._set_form_enabled(True)

    def action_go_back(self) -> None:
        """Return to the main menu."""
        self.app.pop_screen()
