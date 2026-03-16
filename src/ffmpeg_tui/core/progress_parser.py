import re
from typing import Optional


class ProgressInfo:
    """解析后的进度信息。"""

    def __init__(self):
        self.frame: int = 0
        self.fps: float = 0.0
        self.total_size: int = 0
        self.out_time_us: int = 0  # microseconds
        self.speed: float = 0.0
        self.progress: str = ""    # "continue" or "end"

    @property
    def out_time_seconds(self) -> float:
        return self.out_time_us / 1_000_000

    def percentage(self, total_duration: float) -> float:
        if total_duration <= 0:
            return 0.0
        pct = (self.out_time_seconds / total_duration) * 100
        return min(pct, 100.0)


class ProgressParser:
    """解析 FFmpeg -progress pipe:1 的输出。"""

    def __init__(self, total_duration: float = 0.0):
        self.total_duration = total_duration
        self._current = ProgressInfo()

    def parse_line(self, line: str) -> Optional[ProgressInfo]:
        """解析一行进度输出。当遇到 progress= 行时返回完整的 ProgressInfo。

        FFmpeg -progress pipe:1 的输出格式：
        frame=123
        fps=30.0
        total_size=1234567
        out_time_us=5000000
        out_time_ms=5000000  (注意: FFmpeg 的 out_time_ms 实际是微秒)
        out_time=00:00:05.000000
        speed=2.5x
        progress=continue
        """
        line = line.strip()
        if not line or "=" not in line:
            return None

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        try:
            if key == "frame":
                self._current.frame = int(value)
            elif key == "fps":
                self._current.fps = float(value)
            elif key == "total_size":
                self._current.total_size = int(value)
            elif key == "out_time_us":
                self._current.out_time_us = int(value)
            elif key == "out_time_ms":
                # FFmpeg 的 out_time_ms 实际是微秒
                self._current.out_time_us = int(value)
            elif key == "speed":
                # 值格式如 "2.5x" 或 "N/A"
                speed_match = re.match(r"([\d.]+)x", value)
                if speed_match:
                    self._current.speed = float(speed_match.group(1))
            elif key == "progress":
                self._current.progress = value
                result = self._current
                self._current = ProgressInfo()
                return result
        except (ValueError, AttributeError):
            pass

        return None

    def get_percentage(self) -> float:
        return self._current.percentage(self.total_duration)
