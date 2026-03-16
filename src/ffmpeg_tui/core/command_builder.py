from pathlib import Path
from typing import Optional


class CommandBuilder:
    """构建 FFmpeg 命令行参数。"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def build_convert_command(
        self,
        input_file: Path,
        output_file: Path,
        video_codec: Optional[str] = None,
        audio_codec: Optional[str] = None,
    ) -> list[str]:
        """构建格式转换命令。

        基本命令: ffmpeg -i input -c:v codec -c:a codec -y -progress pipe:1 output
        如果不指定编解码器，使用 'copy' 或让 FFmpeg 自动选择。
        """
        cmd = [self.ffmpeg_path, "-i", str(input_file)]
        if video_codec:
            cmd.extend(["-c:v", video_codec])
        if audio_codec:
            cmd.extend(["-c:a", audio_codec])
        cmd.extend(["-y", "-progress", "pipe:1", str(output_file)])
        return cmd

    def build_compress_command(
        self,
        input_file: Path,
        output_file: Path,
        resolution: Optional[str] = None,      # "1920x1080"
        video_bitrate: Optional[str] = None,    # "4000k"
        audio_bitrate: Optional[str] = None,    # "192k"
        framerate: Optional[float] = None,      # 30.0
        preset: str = "medium",                 # x264 preset
    ) -> list[str]:
        """构建视频压缩命令。

        命令: ffmpeg -i input [-vf scale=W:H] [-b:v bitrate] [-b:a bitrate]
              [-r fps] [-preset preset] -y -progress pipe:1 output
        """
        cmd = [self.ffmpeg_path, "-i", str(input_file)]
        if resolution:
            w, h = resolution.split("x")
            cmd.extend(["-vf", f"scale={w}:{h}"])
        if video_bitrate:
            cmd.extend(["-b:v", video_bitrate])
        if audio_bitrate:
            cmd.extend(["-b:a", audio_bitrate])
        if framerate:
            cmd.extend(["-r", str(framerate)])
        cmd.extend(["-preset", preset])
        cmd.extend(["-y", "-progress", "pipe:1", str(output_file)])
        return cmd

    def build_probe_command(
        self,
        input_file: Path,
        ffprobe_path: str = "ffprobe",
    ) -> list[str]:
        """构建 ffprobe 命令获取媒体信息。"""
        return [
            ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(input_file),
        ]
