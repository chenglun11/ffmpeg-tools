"""PyQt6 GUI for FFmpeg TUI Tools."""

import sys


def main() -> None:
    """Launch the GUI application."""
    from PyQt6.QtWidgets import QApplication

    from .main_window import MainWindow
    from .splash import SplashScreen

    app = QApplication(sys.argv)
    app.setApplicationName("FFmpeg Tools")
    app.setOrganizationName("ffmpeg-tui")

    # Show splash screen immediately
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    window = MainWindow(progress_callback=splash.set_progress)
    window.show()
    splash.finish(window)

    sys.exit(app.exec())
