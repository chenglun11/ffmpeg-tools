"""Parameter panel widget for video compression settings."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Select, Static

from ffmpeg_tui.models.conversion_task import CompressionParams
from ffmpeg_tui.models.ffmpeg_info import QUALITY_PRESETS, RESOLUTION_PRESETS

PRESET_OPTIONS: list[tuple[str, str]] = [
    ("ultrafast", "ultrafast"),
    ("superfast", "superfast"),
    ("veryfast", "veryfast"),
    ("faster", "faster"),
    ("fast", "fast"),
    ("medium", "medium"),
    ("slow", "slow"),
    ("slower", "slower"),
    ("veryslow", "veryslow"),
]

RESOLUTION_OPTIONS: list[tuple[str, str]] = [
    ("不更改", ""),
    ("4K (3840x2160)", "3840x2160"),
    ("1080p (1920x1080)", "1920x1080"),
    ("720p (1280x720)", "1280x720"),
    ("480p (854x480)", "854x480"),
]

FRAMERATE_OPTIONS: list[tuple[str, str]] = [
    ("不更改", ""),
    ("60 fps", "60"),
    ("30 fps", "30"),
    ("24 fps", "24"),
]

AUDIO_BITRATE_OPTIONS: list[tuple[str, str]] = [
    ("不更改", ""),
    ("320k (高质量)", "320k"),
    ("192k (标准)", "192k"),
    ("128k (较低)", "128k"),
]

QUALITY_MODE_OPTIONS: list[tuple[str, str]] = [
    ("自定义", "custom"),
    ("高质量", "高质量"),
    ("平衡", "平衡"),
    ("小文件", "小文件"),
]


class ParameterPanel(Widget):
    """Compression parameter configuration panel."""

    class ParamsChanged(Message):
        """Emitted when compression parameters change."""

        def __init__(self, params: CompressionParams) -> None:
            super().__init__()
            self.params = params

    def compose(self) -> ComposeResult:
        with Vertical(id="param-panel"):
            yield Static("压缩参数配置", classes="subtitle")

            # Quality mode preset
            with Vertical(classes="param-row"):
                yield Label("预设模式:")
                yield Select(
                    [(label, value) for label, value in QUALITY_MODE_OPTIONS],
                    value="custom",
                    id="select-quality-mode",
                )

            # Resolution
            with Vertical(classes="param-row"):
                yield Label("分辨率:")
                yield Select(
                    [(label, value) for label, value in RESOLUTION_OPTIONS],
                    value="",
                    id="select-resolution",
                )

            # Video bitrate
            with Vertical(classes="param-row"):
                yield Label("视频码率:")
                yield Input(
                    placeholder="如 4000k 或 5M（留空不更改）",
                    id="input-video-bitrate",
                )

            # Audio bitrate
            with Vertical(classes="param-row"):
                yield Label("音频码率:")
                yield Select(
                    [(label, value) for label, value in AUDIO_BITRATE_OPTIONS],
                    value="",
                    id="select-audio-bitrate",
                )

            # Framerate
            with Vertical(classes="param-row"):
                yield Label("帧率:")
                yield Select(
                    [(label, value) for label, value in FRAMERATE_OPTIONS],
                    value="",
                    id="select-framerate",
                )

            # Encoding preset
            with Vertical(classes="param-row"):
                yield Label("编码预设:")
                yield Select(
                    [(label, value) for label, value in PRESET_OPTIONS],
                    value="medium",
                    id="select-preset",
                )

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select widget changes."""
        if event.select.id == "select-quality-mode" and event.value != "custom":
            self._apply_quality_preset(str(event.value))
        self._emit_params()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        self._emit_params()

    def _apply_quality_preset(self, preset_name: str) -> None:
        """Apply a quality preset to all parameter fields."""
        preset = QUALITY_PRESETS.get(preset_name)
        if not preset:
            return

        vb_input = self.query_one("#input-video-bitrate", Input)
        vb_input.value = preset.video_bitrate or ""

        ab_select = self.query_one("#select-audio-bitrate", Select)
        ab_select.value = preset.audio_bitrate or ""

        preset_select = self.query_one("#select-preset", Select)
        preset_select.value = preset.preset

    def _emit_params(self) -> None:
        """Collect current values and emit ParamsChanged."""
        params = self.get_params()
        self.post_message(self.ParamsChanged(params))

    def get_params(self) -> CompressionParams:
        """Read current parameter values from the widgets."""
        resolution_val = self.query_one("#select-resolution", Select).value
        resolution = str(resolution_val) if resolution_val else None

        vb_val = self.query_one("#input-video-bitrate", Input).value.strip()
        video_bitrate = vb_val if vb_val else None

        ab_val = self.query_one("#select-audio-bitrate", Select).value
        audio_bitrate = str(ab_val) if ab_val else None

        fr_val = self.query_one("#select-framerate", Select).value
        framerate = float(fr_val) if fr_val else None

        preset_val = self.query_one("#select-preset", Select).value
        preset = str(preset_val) if preset_val else "medium"

        return CompressionParams(
            resolution=resolution,
            video_bitrate=video_bitrate,
            audio_bitrate=audio_bitrate,
            framerate=framerate,
            preset=preset,
        )
