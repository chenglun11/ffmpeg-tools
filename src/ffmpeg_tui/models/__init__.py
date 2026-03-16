"""Data models for FFmpeg TUI Tools."""

from .conversion_task import CompressionParams, ConversionTask, TaskStatus
from .ffmpeg_info import (
    QUALITY_PRESETS,
    RESOLUTION_PRESETS,
    FFmpegInfo,
    ProgressInfo,
)
from .format_config import (
    AUDIO_FORMATS,
    VIDEO_FORMATS,
    AudioFormat,
    FormatInfo,
    VideoFormat,
)

__all__ = [
    "AudioFormat",
    "AUDIO_FORMATS",
    "CompressionParams",
    "ConversionTask",
    "FFmpegInfo",
    "FormatInfo",
    "ProgressInfo",
    "QUALITY_PRESETS",
    "RESOLUTION_PRESETS",
    "TaskStatus",
    "VideoFormat",
    "VIDEO_FORMATS",
]
