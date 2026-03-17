import json
import subprocess
from pathlib import Path

MEDIA_EXTENSIONS = {
    "video": {".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv", ".webm", ".3gp"},
    "audio": {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".amr"},
    "image": {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"},
}
ALL_MEDIA_EXTENSIONS = MEDIA_EXTENSIONS["video"] | MEDIA_EXTENSIONS["audio"] | MEDIA_EXTENSIONS["image"]

def is_media_file(path: Path) -> bool:
    """判断文件是否是支持的媒体文件"""
    return path.suffix.lower() in ALL_MEDIA_EXTENSIONS

def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in MEDIA_EXTENSIONS["video"]

def is_audio_file(path: Path) -> bool:
    return path.suffix.lower() in MEDIA_EXTENSIONS["audio"]

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小为人类可读格式"""
    if size_bytes < 0:
        return "0.0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"

def format_duration(seconds: float) -> str:
    """格式化时长为 HH:MM:SS 格式"""
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def get_media_duration(file_path: Path, ffprobe_path: str = "ffprobe") -> float:
    """使用 ffprobe 获取媒体文件时长（秒）"""
    try:
        result = subprocess.run(
            [ffprobe_path, "-v", "quiet", "-print_format", "json", "-show_format", str(file_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return float(data.get("format", {}).get("duration", 0))
    except (json.JSONDecodeError, ValueError, FileNotFoundError):
        pass
    return 0.0

def get_file_info(path: Path, ffprobe_path: str = "ffprobe") -> dict:
    """获取文件信息（大小、格式、时长等）"""
    info: dict = {
        "name": path.name,
        "path": str(path),
        "suffix": path.suffix.lower(),
        "size": 0,
        "size_formatted": "0.0 B",
        "is_video": is_video_file(path),
        "is_audio": is_audio_file(path),
        "duration": 0.0,
        "duration_formatted": "00:00",
    }
    if path.exists() and path.is_file():
        size = path.stat().st_size
        info["size"] = size
        info["size_formatted"] = format_file_size(size)
        duration = get_media_duration(path, ffprobe_path)
        info["duration"] = duration
        info["duration_formatted"] = format_duration(duration)
    return info

def generate_output_path(input_path: Path, output_format: str, suffix: str = "_converted") -> Path:
    """根据输入文件生成输出文件路径"""
    if not output_format.startswith("."):
        output_format = f".{output_format}"
    return input_path.with_stem(input_path.stem + suffix).with_suffix(output_format)

def validate_input_file(path: Path) -> tuple[bool, str]:
    """验证输入文件。返回 (是否有效, 错误信息)"""
    if not path.exists():
        return False, f"文件不存在: {path}"
    if not path.is_file():
        return False, f"不是一个文件: {path}"
    if not is_media_file(path):
        return False, f"不支持的文件格式: {path.suffix}"
    return True, ""
