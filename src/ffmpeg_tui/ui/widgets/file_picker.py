"""File picker widget for selecting media files."""

from pathlib import Path
from typing import Iterable

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, DirectoryTree, Input, Static

from ffmpeg_tui.utils.file_utils import ALL_MEDIA_EXTENSIONS


class MediaDirectoryTree(DirectoryTree):
    """DirectoryTree filtered to show only media files and directories."""

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """Show directories and media files only."""
        return [
            p
            for p in paths
            if p.is_dir() or p.suffix.lower() in ALL_MEDIA_EXTENSIONS
        ]


class FilePicker(Widget):
    """A compound widget with a text input for file path and a browse button."""

    DEFAULT_CSS = """
    FilePicker {
        height: auto;
        width: 100%;
    }
    FilePicker .file-picker-row {
        layout: horizontal;
        height: auto;
        width: 100%;
    }
    FilePicker .file-picker-row Input {
        width: 1fr;
        margin: 0 1 0 0;
    }
    FilePicker .file-picker-row Button {
        width: auto;
        min-width: 12;
        margin: 0;
    }
    FilePicker .tree-container {
        height: 16;
        width: 100%;
        display: none;
        border: round $primary;
        margin: 1 0;
    }
    FilePicker .tree-container.visible {
        display: block;
    }
    """

    class FileSelected(Message):
        """Posted when a file is selected."""

        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    def __init__(
        self,
        placeholder: str = "输入文件路径或点击浏览...",
        *,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Horizontal(classes="file-picker-row"):
            yield Input(placeholder=self._placeholder, id="file-input")
            yield Button("浏览", id="btn-browse", variant="primary")
        with Vertical(classes="tree-container", id="tree-container"):
            yield Static("选择文件 (点击文件或按 Escape 关闭):", classes="subtitle")
            yield MediaDirectoryTree(Path.home(), id="dir-tree")

    @on(Button.Pressed, "#btn-browse")
    def _toggle_tree(self) -> None:
        container = self.query_one("#tree-container")
        container.toggle_class("visible")

    @on(DirectoryTree.FileSelected, "#dir-tree")
    def _on_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        event.stop()
        path = event.path
        if path.suffix.lower() in ALL_MEDIA_EXTENSIONS:
            self.query_one("#file-input", Input).value = str(path)
            self.query_one("#tree-container").remove_class("visible")
            self.post_message(self.FileSelected(path))
        else:
            self.notify(f"不支持的文件格式: {path.suffix}", severity="warning")

    @on(Input.Submitted, "#file-input")
    def _on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        value = event.value.strip()
        if value:
            path = Path(value)
            self.post_message(self.FileSelected(path))

    @property
    def value(self) -> str:
        """Return the current file path string."""
        return self.query_one("#file-input", Input).value

    @value.setter
    def value(self, new_value: str) -> None:
        self.query_one("#file-input", Input).value = new_value
