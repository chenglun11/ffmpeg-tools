"""QThread workers for bridging async FFmpeg operations to the Qt event loop."""

import asyncio
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from ffmpeg_tui.core.ffmpeg_executor import FFmpegExecutor
from ffmpeg_tui.core.ffmpeg_manager import FFmpegManager
from ffmpeg_tui.core.progress_parser import ProgressInfo


class FFmpegWorker(QThread):
    """Run an FFmpeg command in a background thread with its own asyncio loop.

    Signals:
        progress(pct, frame, fps, speed, eta_seconds)
        finished(success)
        error(message)
    """

    progress = pyqtSignal(float, int, float, float, float)
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(
        self,
        command: list[str],
        total_duration: float = 0.0,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._command = command
        self._total_duration = total_duration
        self._executor = FFmpegExecutor()

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(
                self._executor.execute(
                    self._command,
                    total_duration=self._total_duration,
                    progress_callback=self._on_progress,
                )
            )
            self.finished.emit(success)
        except Exception as exc:
            self.error.emit(str(exc))
            self.finished.emit(False)
        finally:
            loop.close()

    def _on_progress(self, info: ProgressInfo) -> None:
        pct = info.percentage(self._total_duration)
        eta = 0.0
        if info.speed > 0 and self._total_duration > 0:
            elapsed = info.out_time_seconds
            remaining = self._total_duration - elapsed
            eta = remaining / info.speed
        self.progress.emit(pct, info.frame, info.fps, info.speed, eta)

    def cancel(self) -> None:
        self._executor.cancel()


class DownloadWorker(QThread):
    """Download FFmpeg in a background thread.

    Signals:
        progress(downloaded_bytes, total_bytes)  — total may be -1 if unknown
        finished(success, message)
    """

    progress = pyqtSignal(int, int)
    finished = pyqtSignal(bool, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._manager = FFmpegManager()

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            path = loop.run_until_complete(
                self._manager.download_ffmpeg(progress_callback=self._on_progress)
            )
            self.finished.emit(True, str(path))
        except Exception as exc:
            self.finished.emit(False, str(exc))
        finally:
            loop.close()

    def _on_progress(self, downloaded: int, total: Optional[int]) -> None:
        self.progress.emit(downloaded, total if total is not None else -1)


class UpdateCheckWorker(QThread):
    """Check for application updates in a background thread.

    Signals:
        finished(has_update, info)  — info is UpdateInfo or None (on error)
        error(message)  — user-friendly error message
    """

    finished = pyqtSignal(bool, object)
    error = pyqtSignal(str)

    def run(self) -> None:
        from ffmpeg_tui.gui.updater import UpdateChecker, UpdateCheckError, _parse_version
        from ffmpeg_tui import __version__

        try:
            info = UpdateChecker().check_update()
            has_update = _parse_version(info.latest_version) > _parse_version(__version__)
            self.finished.emit(has_update, info)
        except UpdateCheckError as e:
            self.error.emit(str(e))
            self.finished.emit(False, None)
        except Exception as e:
            self.error.emit(f"检查更新时出错: {e}")
            self.finished.emit(False, None)
