"""PyQt6 GUI for FFmpeg TUI Tools."""

import sys


def main() -> None:
    """Launch the GUI application."""
    from PyQt6.QtWidgets import QApplication

    from .main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("FFmpeg Tools")
    app.setOrganizationName("ffmpeg-tui")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
