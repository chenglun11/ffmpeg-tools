"""PyQt6 GUI for FFmpeg TUI Tools."""

import sys


def main() -> None:
    """Launch the GUI application."""
    import sys
    from PyQt6.QtWidgets import QApplication
    from .main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("FFmpeg Tools")
    app.setOrganizationName("ffmpeg-tui")

    # 直接创建主窗口，不使用 splash（打包环境下可能有问题）
    window = MainWindow(progress_callback=None)
    window.show()

    sys.exit(app.exec())
