"""Format selector widget for choosing output formats."""

from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Select, Static

from ffmpeg_tui.models.format_config import (
    AUDIO_FORMATS,
    VIDEO_FORMATS,
    AudioFormat,
    FormatInfo,
    VideoFormat,
)


def _build_format_options() -> list[tuple[str, str]]:
    """Build a list of (label, value) tuples for the Select widget."""
    options: list[tuple[str, str]] = []
    # Video formats
    for fmt, info in VIDEO_FORMATS.items():
        options.append((f"[视频] {info.name} - {info.description}", fmt.value))
    # Audio formats
    for fmt, info in AUDIO_FORMATS.items():
        options.append((f"[音频] {info.name} - {info.description}", fmt.value))
    return options


def get_format_info(format_value: str) -> FormatInfo | None:
    """Look up FormatInfo by format string value."""
    for fmt, info in VIDEO_FORMATS.items():
        if fmt.value == format_value:
            return info
    for fmt, info in AUDIO_FORMATS.items():
        if fmt.value == format_value:
            return info
    return None


def is_audio_only(format_value: str) -> bool:
    """Return True if the format is audio-only."""
    for fmt in AudioFormat:
        if fmt.value == format_value:
            return True
    return False


class FormatSelector(Widget):
    """Widget for selecting output format with description display."""

    DEFAULT_CSS = """
    FormatSelector {
        height: auto;
        width: 100%;
    }
    FormatSelector Select {
        width: 100%;
        margin: 0;
    }
    FormatSelector #format-desc {
        height: auto;
        padding: 0 1;
        color: $text-muted;
        text-style: italic;
    }
    """

    class FormatChanged(Message):
        """Posted when the selected format changes."""

        def __init__(self, format_value: str, format_info: FormatInfo) -> None:
            super().__init__()
            self.format_value = format_value
            self.format_info = format_info

    def compose(self) -> ComposeResult:
        options = _build_format_options()
        yield Select(
            [(label, value) for label, value in options],
            prompt="选择输出格式...",
            id="format-select",
        )
        yield Static("", id="format-desc")

    @on(Select.Changed, "#format-select")
    def _on_format_changed(self, event: Select.Changed) -> None:
        event.stop()
        if event.value is not Select.BLANK:
            info = get_format_info(str(event.value))
            if info:
                desc = f"编解码器: "
                parts = []
                if info.default_video_codec:
                    parts.append(f"视频={info.default_video_codec}")
                if info.default_audio_codec:
                    parts.append(f"音频={info.default_audio_codec}")
                desc += ", ".join(parts)
                self.query_one("#format-desc", Static).update(desc)
                self.post_message(self.FormatChanged(str(event.value), info))
        else:
            self.query_one("#format-desc", Static).update("")

    @property
    def selected_format(self) -> str | None:
        """Return the currently selected format value, or None."""
        select = self.query_one("#format-select", Select)
        if select.value is Select.BLANK:
            return None
        return str(select.value)
