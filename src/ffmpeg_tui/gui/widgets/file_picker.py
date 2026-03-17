"""File picker widget: QLineEdit + Browse button + QFileDialog."""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from ffmpeg_tui.utils.file_utils import ALL_MEDIA_EXTENSIONS


def _build_filter_string() -> str:
    exts = " ".join(f"*{e}" for e in sorted(ALL_MEDIA_EXTENSIONS))
    return f"媒体文件 ({exts});;所有文件 (*)"


class FilePickerWidget(QWidget):
    """A line-edit + browse button that emits *file_selected* with the chosen path."""

    file_selected = pyqtSignal(Path)

    def __init__(self, label: str = "输入文件:", parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(label)
        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText("选择或拖入媒体文件…")
        self._browse_btn = QPushButton("浏览…")

        layout.addWidget(self._label)
        layout.addWidget(self._line_edit, stretch=1)
        layout.addWidget(self._browse_btn)

        self._browse_btn.clicked.connect(self._browse)
        self._line_edit.editingFinished.connect(self._on_text_changed)

        self.setAcceptDrops(True)

    def path(self) -> Optional[Path]:
        text = self._line_edit.text().strip()
        return Path(text) if text else None

    def set_path(self, path: Path) -> None:
        self._line_edit.setText(str(path))

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择媒体文件", "", _build_filter_string()
        )
        if path:
            self._line_edit.setText(path)
            self.file_selected.emit(Path(path))

    def _on_text_changed(self) -> None:
        text = self._line_edit.text().strip()
        if text:
            self.file_selected.emit(Path(text))

    # Drag & drop support
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            path = Path(url.toLocalFile())
            if path.suffix.lower() in ALL_MEDIA_EXTENSIONS:
                event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile())
            self._line_edit.setText(str(path))
            self.file_selected.emit(path)
