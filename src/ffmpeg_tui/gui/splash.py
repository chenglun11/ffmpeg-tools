"""Startup splash screen with loading progress."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath
from PyQt6.QtWidgets import QSplashScreen


class SplashScreen(QSplashScreen):
    """A styled splash screen that shows loading progress during startup."""

    _WIDTH = 400
    _HEIGHT = 220
    _BG = QColor("#ffffff")
    _ACCENT = QColor("#7c3aed")
    _ACCENT_LIGHT = QColor("#a78bfa")
    _TEXT_PRIMARY = QColor("#1f2937")
    _TEXT_SECONDARY = QColor("#6b7280")
    _TRACK = QColor("#f3f4f6")

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(self._WIDTH, self._HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self._progress = 0
        self._message = "正在启动..."

    def set_progress(self, value: int, message: str = "") -> None:
        """Update progress (0-100) and optional status message."""
        self._progress = max(0, min(100, value))
        if message:
            self._message = message
        self.repaint()
        # Process events so the splash actually repaints
        if self.parent() is None:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if app:
                app.processEvents()

    def drawContents(self, painter: QPainter) -> None:  # noqa: N802
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background with rounded corners
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, self._WIDTH, self._HEIGHT, 12, 12)
        painter.setClipPath(path)
        painter.fillRect(self.rect(), self._BG)

        # Top accent bar
        painter.fillRect(0, 0, self._WIDTH, 4, self._ACCENT)

        # App icon placeholder (purple circle with play icon)
        cx, cy = self._WIDTH // 2, 60
        painter.setBrush(self._ACCENT)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - 24, cy - 24, 48, 48)

        # Triangle play icon
        painter.setBrush(QColor("#ffffff"))
        play = QPainterPath()
        play.moveTo(cx - 8, cy - 12)
        play.lineTo(cx - 8, cy + 12)
        play.lineTo(cx + 14, cy)
        play.closeSubpath()
        painter.drawPath(play)

        # Title
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(self._TEXT_PRIMARY)
        painter.drawText(
            0, 100, self._WIDTH, 30, Qt.AlignmentFlag.AlignCenter, "FFmpeg Tools"
        )

        # Status message
        font.setPointSize(11)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(self._TEXT_SECONDARY)
        painter.drawText(
            0, 130, self._WIDTH, 24, Qt.AlignmentFlag.AlignCenter, self._message
        )

        # Progress bar track
        bar_x, bar_y = 60, 170
        bar_w, bar_h = self._WIDTH - 120, 6
        track_path = QPainterPath()
        track_path.addRoundedRect(bar_x, bar_y, bar_w, bar_h, 3, 3)
        painter.fillPath(track_path, self._TRACK)

        # Progress bar fill
        if self._progress > 0:
            fill_w = bar_w * self._progress / 100
            fill_path = QPainterPath()
            fill_path.addRoundedRect(bar_x, bar_y, fill_w, bar_h, 3, 3)
            grad = QLinearGradient(bar_x, 0, bar_x + fill_w, 0)
            grad.setColorAt(0, self._ACCENT)
            grad.setColorAt(1, self._ACCENT_LIGHT)
            painter.fillPath(fill_path, grad)

        # Version / footer
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor("#d1d5db"))
        painter.drawText(
            0,
            self._HEIGHT - 28,
            self._WIDTH,
            20,
            Qt.AlignmentFlag.AlignCenter,
            f"{self._progress}%",
        )

    # Make the splash window itself rounded
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, self._WIDTH, self._HEIGHT, 12, 12)
        painter.setClipPath(path)
        self.drawContents(painter)
        painter.end()
