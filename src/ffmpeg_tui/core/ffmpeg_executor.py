import asyncio
import json
import subprocess
from pathlib import Path
from typing import Optional, Callable, Awaitable

from .progress_parser import ProgressParser, ProgressInfo


class FFmpegExecutor:
    """异步执行 FFmpeg 命令并监控进度。"""

    def __init__(self):
        self._process: Optional[asyncio.subprocess.Process] = None
        self._cancelled = False

    async def execute(
        self,
        command: list[str],
        total_duration: float = 0.0,
        progress_callback: Optional[Callable[[ProgressInfo], Awaitable[None] | None]] = None,
    ) -> bool:
        """执行 FFmpeg 命令。

        Args:
            command: FFmpeg 命令参数列表
            total_duration: 输入文件总时长（秒），用于计算百分比
            progress_callback: 进度回调函数，接收 ProgressInfo

        Returns:
            True 表示成功，False 表示失败
        """
        self._cancelled = False
        parser = ProgressParser(total_duration)

        self._process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            # 读取 stdout（progress 输出）
            while True:
                if self._cancelled:
                    self._process.terminate()
                    await self._process.wait()
                    return False

                line = await self._process.stdout.readline()
                if not line:
                    break

                decoded = line.decode("utf-8", errors="replace")
                info = parser.parse_line(decoded)
                if info and progress_callback:
                    result = progress_callback(info)
                    if asyncio.iscoroutine(result):
                        await result

            await self._process.wait()
            return self._process.returncode == 0

        except Exception:
            if self._process.returncode is None:
                self._process.terminate()
                await self._process.wait()
            return False

    def cancel(self):
        """取消当前执行。"""
        self._cancelled = True
        if self._process and self._process.returncode is None:
            self._process.terminate()

    @staticmethod
    def get_duration(input_file: Path, ffprobe_path: str = "ffprobe") -> float:
        """使用 ffprobe 获取媒体文件时长（秒）。"""
        try:
            result = subprocess.run(
                [
                    ffprobe_path,
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    str(input_file),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data.get("format", {}).get("duration", 0))
        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            pass
        return 0.0
