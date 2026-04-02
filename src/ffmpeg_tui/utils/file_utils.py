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

def probe_media_streams(file_path: Path, ffprobe_path: str = "ffprobe") -> dict:
    """使用 ffprobe 获取媒体文件的详细流信息。

    Returns:
        dict with keys: format_name, duration, bit_rate, size,
        video (dict or None), audio (dict or None).
    """
    result_data: dict = {
        "format_name": "",
        "duration": 0.0,
        "bit_rate": 0,
        "size": 0,
        "video": None,
        "audio": None,
    }
    try:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return result_data
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError, FileNotFoundError, subprocess.TimeoutExpired):
        return result_data

    fmt = data.get("format", {})
    result_data["format_name"] = fmt.get("format_long_name", fmt.get("format_name", ""))
    result_data["duration"] = float(fmt.get("duration", 0))
    result_data["bit_rate"] = int(fmt.get("bit_rate", 0))
    result_data["size"] = int(fmt.get("size", 0))

    for stream in data.get("streams", []):
        codec_type = stream.get("codec_type")
        if codec_type == "video" and result_data["video"] is None:
            width = int(stream.get("width", 0))
            height = int(stream.get("height", 0))
            # Parse frame rate from r_frame_rate like "30/1" or "30000/1001"
            fps = 0.0
            r_fps = stream.get("r_frame_rate", "0/1")
            try:
                if "/" in r_fps:
                    num, den = r_fps.split("/", 1)
                    if int(den) > 0:
                        fps = round(int(num) / int(den), 2)
            except (ValueError, ZeroDivisionError):
                fps = 0.0
            result_data["video"] = {
                "codec": stream.get("codec_long_name", stream.get("codec_name", "")),
                "codec_short": stream.get("codec_name", ""),
                "width": width,
                "height": height,
                "fps": fps,
                "pix_fmt": stream.get("pix_fmt", ""),
                "bit_rate": int(stream.get("bit_rate", 0)),
            }
        elif codec_type == "audio" and result_data["audio"] is None:
            result_data["audio"] = {
                "codec": stream.get("codec_long_name", stream.get("codec_name", "")),
                "codec_short": stream.get("codec_name", ""),
                "sample_rate": int(stream.get("sample_rate", 0)),
                "channels": int(stream.get("channels", 0)),
                "channel_layout": stream.get("channel_layout", ""),
                "bit_rate": int(stream.get("bit_rate", 0)),
            }
    return result_data


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
