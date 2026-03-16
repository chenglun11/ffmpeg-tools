"""FFmpeg information and progress tracking models."""

from pathlib import Path

from pydantic import BaseModel

from .conversion_task import CompressionParams


class FFmpegInfo(BaseModel):
    version: str
    path: Path
    build_info: str = ""


class ProgressInfo(BaseModel):
    frame: int = 0
    fps: float = 0.0
    total_size: int = 0
    out_time_ms: int = 0
    speed: float = 0.0
    percentage: float = 0.0


RESOLUTION_PRESETS: dict[str, str] = {
    "4K": "3840x2160",
    "1080p": "1920x1080",
    "720p": "1280x720",
    "480p": "854x480",
}

QUALITY_PRESETS: dict[str, CompressionParams] = {
    "高质量": CompressionParams(
        video_bitrate="8000k", audio_bitrate="320k", preset="slow"
    ),
    "平衡": CompressionParams(
        video_bitrate="4000k", audio_bitrate="192k", preset="medium"
    ),
    "小文件": CompressionParams(
        video_bitrate="2000k", audio_bitrate="128k", preset="fast"
    ),
}
