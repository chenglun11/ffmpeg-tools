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
        """使用 ffprobe 获取媒体文件时长（秒）。

        Returns:
            文件时长（秒），失败时返回 0.0
        """
        try:
            # 确保路径存在
            if not input_file.exists():
                return 0.0

            # Windows 路径处理：使用绝对路径并转换为字符串
            file_path_str = str(input_file.absolute())

            result = subprocess.run(
                [
                    ffprobe_path,
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    file_path_str,
                ],
                capture_output=True,
                text=True,
                timeout=10,
                # Windows 上避免弹出控制台窗口
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = data.get("format", {}).get("duration", 0)
                return float(duration) if duration else 0.0

        except json.JSONDecodeError:
            # JSON 解析失败
            pass
        except (ValueError, TypeError):
            # 数值转换失败
            pass
        except FileNotFoundError:
            # ffprobe 不存在
            pass
        except subprocess.TimeoutExpired:
            # 超时
            pass
        except Exception:
            # 捕获所有其他异常，避免崩溃
            pass

        return 0.0
