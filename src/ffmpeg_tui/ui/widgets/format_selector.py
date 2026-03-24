"""Format selector widget: container + video codec + audio codec for TUI."""

from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Select, Static

from ffmpeg_tui.models.format_config import (
    AUDIO_CODECS,
    CONTAINERS,
    VIDEO_CODECS,
    ContainerInfo,
)


def _build_container_options() -> list[tuple[str, str]]:
    """Build (label, key) tuples for the container Select."""
    options: list[tuple[str, str]] = []
    # Video containers first
    for key, info in CONTAINERS.items():
        if not info.is_audio_only:
            options.append((f"[视频] {info.name} - {info.description}", key))
    # Audio containers
    for key, info in CONTAINERS.items():
        if info.is_audio_only:
            options.append((f"[音频] {info.name} - {info.description}", key))
    return options


def _build_video_codec_options(container: ContainerInfo) -> list[tuple[str, str]]:
    """Build (label, codec_name) for compatible video codecs."""
    options: list[tuple[str, str]] = []
    for codec_name in container.compatible_video_codecs:
        codec = VIDEO_CODECS.get(codec_name)
        if codec:
            options.append((f"{codec.display_name} ({codec.codec_name})", codec_name))
    return options


def _build_audio_codec_options(container: ContainerInfo) -> list[tuple[str, str]]:
    """Build (label, codec_name) for compatible audio codecs."""
    options: list[tuple[str, str]] = []
    for codec_name in container.compatible_audio_codecs:
        codec = AUDIO_CODECS.get(codec_name)
        if codec:
            options.append((f"{codec.display_name} ({codec.codec_name})", codec_name))
    return options


# Legacy helpers kept for any external imports
def get_format_info(format_value: str):
    """Look up ContainerInfo by key. Returns ContainerInfo or None."""
    return CONTAINERS.get(format_value)


def is_audio_only(format_value: str) -> bool:
    """Return True if the container is audio-only."""
    info = CONTAINERS.get(format_value)
    return info.is_audio_only if info else False


class FormatSelector(Widget):
    """Widget with three selects: container, video codec, audio codec."""

    DEFAULT_CSS = """
    FormatSelector {
        height: auto;
        width: 100%;
    }
    FormatSelector Select {
        width: 100%;
        margin: 0 0 1 0;
    }
    FormatSelector .codec-label {
        height: auto;
        padding: 0 1;
        color: $accent;
        text-style: bold;
        width: auto;
    }
    FormatSelector #format-desc {
        height: auto;
        padding: 0 1;
        color: $text-muted;
        text-style: italic;
    }
    """

    class FormatChanged(Message):
        """Posted when any selection changes."""

        def __init__(self, extension: str, video_codec: str | None, audio_codec: str | None) -> None:
            super().__init__()
            self.extension = extension
            self.video_codec = video_codec
            self.audio_codec = audio_codec
            # Compat attributes
            self.format_value = extension
            self.format_info = CONTAINERS.get(extension)

    _updating: bool = False  # guard against recursive signals during codec updates

    def compose(self) -> ComposeResult:
        yield Static("容器格式", classes="codec-label")
        yield Select(
            [(label, value) for label, value in _build_container_options()],
            prompt="选择容器格式...",
            id="container-select",
        )
        yield Static("", id="format-desc")

        yield Static("视频编码", classes="codec-label")
        yield Select([], prompt="选择视频编码...", id="video-codec-select")

        yield Static("音频编码", classes="codec-label")
        yield Select([], prompt="选择音频编码...", id="audio-codec-select")

    @on(Select.Changed, "#container-select")
    def _on_container_changed(self, event: Select.Changed) -> None:
        event.stop()
        if event.value is Select.BLANK:
            self.query_one("#format-desc", Static).update("")
            return
        key = str(event.value)
        info = CONTAINERS.get(key)
        if not info:
            return

        self.query_one("#format-desc", Static).update(info.description)
        self._update_codec_selects(info)
        self._emit_change()

    @on(Select.Changed, "#video-codec-select")
    def _on_video_codec_changed(self, event: Select.Changed) -> None:
        event.stop()
        if not self._updating:
            self._emit_change()

    @on(Select.Changed, "#audio-codec-select")
    def _on_audio_codec_changed(self, event: Select.Changed) -> None:
        event.stop()
        if not self._updating:
            self._emit_change()

    def _update_codec_selects(self, container: ContainerInfo) -> None:
        self._updating = True
        video_select = self.query_one("#video-codec-select", Select)
        audio_select = self.query_one("#audio-codec-select", Select)

        if container.is_audio_only:
            video_select.set_options([("(纯音频，无视频)", "__none__")])
            video_select.value = "__none__"
            video_select.disabled = True
        else:
            vopts = _build_video_codec_options(container)
            video_select.set_options(vopts)
            video_select.disabled = False
            if container.default_video_codec:
                video_select.value = container.default_video_codec

        aopts = _build_audio_codec_options(container)
        audio_select.set_options(aopts)
        if container.default_audio_codec:
            audio_select.value = container.default_audio_codec
        self._updating = False

    def _emit_change(self) -> None:
        container_sel = self.query_one("#container-select", Select)
        if container_sel.value is Select.BLANK:
            return

        key = str(container_sel.value)
        info = CONTAINERS.get(key)
        if not info:
            return

        video_codec = None
        if not info.is_audio_only:
            vs = self.query_one("#video-codec-select", Select)
            if vs.value is not Select.BLANK:
                video_codec = str(vs.value)

        audio_codec = None
        aus = self.query_one("#audio-codec-select", Select)
        if aus.value is not Select.BLANK:
            audio_codec = str(aus.value)

        self.post_message(self.FormatChanged(info.extension, video_codec, audio_codec))

    @property
    def selected_format(self) -> str | None:
        """Return the currently selected container key, or None."""
        select = self.query_one("#container-select", Select)
        if select.value is Select.BLANK:
            return None
        return str(select.value)

    @property
    def selected_codecs(self) -> tuple[str | None, str | None]:
        """Return (video_codec, audio_codec)."""
        video_codec = None
        vs = self.query_one("#video-codec-select", Select)
        if vs.value is not Select.BLANK and str(vs.value) != "__none__":
            video_codec = str(vs.value)

        audio_codec = None
        aus = self.query_one("#audio-codec-select", Select)
        if aus.value is not Select.BLANK:
            audio_codec = str(aus.value)

        return (video_codec, audio_codec)
