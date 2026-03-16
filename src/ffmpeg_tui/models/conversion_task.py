"""Conversion task models for tracking FFmpeg operations."""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CompressionParams(BaseModel):
    resolution: str | None = None
    video_bitrate: str | None = None
    audio_bitrate: str | None = None
    framerate: float | None = None
    preset: str = "medium"


class ConversionTask(BaseModel):
    input_file: Path
    output_file: Path
    output_format: str
    compression_params: CompressionParams | None = None
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    error: str | None = None
