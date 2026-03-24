"""Format configuration models for video and audio formats."""

from enum import Enum

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Legacy enums & FormatInfo (kept for backward compatibility)
# ---------------------------------------------------------------------------

class VideoFormat(str, Enum):
    MP4 = "mp4"
    AVI = "avi"
    MKV = "mkv"
    MOV = "mov"
    FLV = "flv"
    WMV = "wmv"
    WEBM = "webm"


class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    AAC = "aac"
    FLAC = "flac"
    OGG = "ogg"
    M4A = "m4a"


class FormatInfo(BaseModel):
    name: str
    extension: str
    description: str
    default_video_codec: str | None = None
    default_audio_codec: str | None = None


VIDEO_FORMATS: dict[VideoFormat, FormatInfo] = {
    VideoFormat.MP4: FormatInfo(
        name="MP4",
        extension="mp4",
        description="MPEG-4 Part 14, widely supported format",
        default_video_codec="libx264",
        default_audio_codec="aac",
    ),
    VideoFormat.AVI: FormatInfo(
        name="AVI",
        extension="avi",
        description="Audio Video Interleave, legacy Microsoft format",
        default_video_codec="libx264",
        default_audio_codec="mp3",
    ),
    VideoFormat.MKV: FormatInfo(
        name="MKV",
        extension="mkv",
        description="Matroska Video, flexible open container format",
        default_video_codec="libx264",
        default_audio_codec="aac",
    ),
    VideoFormat.MOV: FormatInfo(
        name="MOV",
        extension="mov",
        description="QuickTime File Format, Apple's multimedia container",
        default_video_codec="libx264",
        default_audio_codec="aac",
    ),
    VideoFormat.FLV: FormatInfo(
        name="FLV",
        extension="flv",
        description="Flash Video, used for web streaming",
        default_video_codec="libx264",
        default_audio_codec="aac",
    ),
    VideoFormat.WMV: FormatInfo(
        name="WMV",
        extension="wmv",
        description="Windows Media Video, Microsoft's video format",
        default_video_codec="wmv2",
        default_audio_codec="wmav2",
    ),
    VideoFormat.WEBM: FormatInfo(
        name="WEBM",
        extension="webm",
        description="WebM, open format optimized for web use",
        default_video_codec="libvpx-vp9",
        default_audio_codec="libopus",
    ),
}

AUDIO_FORMATS: dict[AudioFormat, FormatInfo] = {
    AudioFormat.MP3: FormatInfo(
        name="MP3",
        extension="mp3",
        description="MPEG Audio Layer III, most common audio format",
        default_audio_codec="libmp3lame",
    ),
    AudioFormat.WAV: FormatInfo(
        name="WAV",
        extension="wav",
        description="Waveform Audio, uncompressed lossless format",
        default_audio_codec="pcm_s16le",
    ),
    AudioFormat.AAC: FormatInfo(
        name="AAC",
        extension="aac",
        description="Advanced Audio Coding, high-quality lossy format",
        default_audio_codec="aac",
    ),
    AudioFormat.FLAC: FormatInfo(
        name="FLAC",
        extension="flac",
        description="Free Lossless Audio Codec, compressed lossless format",
        default_audio_codec="flac",
    ),
    AudioFormat.OGG: FormatInfo(
        name="OGG",
        extension="ogg",
        description="Ogg Vorbis, open-source lossy format",
        default_audio_codec="libvorbis",
    ),
    AudioFormat.M4A: FormatInfo(
        name="M4A",
        extension="m4a",
        description="MPEG-4 Audio, AAC audio in MP4 container",
        default_audio_codec="aac",
    ),
}


# ---------------------------------------------------------------------------
# New container + codec separation models
# ---------------------------------------------------------------------------

class CodecInfo(BaseModel):
    """A video or audio codec entry."""
    codec_name: str       # ffmpeg codec id, e.g. "libx264"
    display_name: str     # human-readable, e.g. "H.264"
    description: str = ""


class ContainerInfo(BaseModel):
    """A container format with its compatible codecs."""
    name: str
    extension: str
    description: str
    is_audio_only: bool = False
    compatible_video_codecs: list[str] = []   # codec_name references
    compatible_audio_codecs: list[str] = []
    default_video_codec: str | None = None
    default_audio_codec: str | None = None


# -- Video codecs ----------------------------------------------------------

VIDEO_CODECS: dict[str, CodecInfo] = {
    "libx264": CodecInfo(
        codec_name="libx264",
        display_name="H.264",
        description="最常用的视频编码，兼容性极佳",
    ),
    "libx265": CodecInfo(
        codec_name="libx265",
        display_name="H.265 / HEVC",
        description="高压缩率，体积更小，但编码较慢",
    ),
    "libvpx": CodecInfo(
        codec_name="libvpx",
        display_name="VP8",
        description="Google 开源编码，用于 WebM",
    ),
    "libvpx-vp9": CodecInfo(
        codec_name="libvpx-vp9",
        display_name="VP9",
        description="VP8 升级版，压缩效率更高",
    ),
    "libaom-av1": CodecInfo(
        codec_name="libaom-av1",
        display_name="AV1",
        description="新一代开放编码，压缩率最高但编码极慢",
    ),
    "mpeg4": CodecInfo(
        codec_name="mpeg4",
        display_name="MPEG-4",
        description="传统编码，AVI 常用",
    ),
    "prores_ks": CodecInfo(
        codec_name="prores_ks",
        display_name="ProRes",
        description="Apple 专业后期编码，高质量",
    ),
    "wmv2": CodecInfo(
        codec_name="wmv2",
        display_name="WMV2",
        description="Windows Media Video 编码",
    ),
}

# -- Audio codecs ----------------------------------------------------------

AUDIO_CODECS: dict[str, CodecInfo] = {
    "aac": CodecInfo(
        codec_name="aac",
        display_name="AAC",
        description="高质量有损音频，MP4/MOV 默认",
    ),
    "libmp3lame": CodecInfo(
        codec_name="libmp3lame",
        display_name="MP3",
        description="最常见的有损音频格式",
    ),
    "libopus": CodecInfo(
        codec_name="libopus",
        display_name="Opus",
        description="低延迟高质量编码，适合语音和音乐",
    ),
    "libvorbis": CodecInfo(
        codec_name="libvorbis",
        display_name="Vorbis",
        description="开源有损音频编码",
    ),
    "flac": CodecInfo(
        codec_name="flac",
        display_name="FLAC",
        description="无损音频压缩",
    ),
    "pcm_s16le": CodecInfo(
        codec_name="pcm_s16le",
        display_name="PCM 16-bit",
        description="未压缩音频 (WAV 常用)",
    ),
    "ac3": CodecInfo(
        codec_name="ac3",
        display_name="AC3 / Dolby",
        description="杜比数字音频",
    ),
    "wmav2": CodecInfo(
        codec_name="wmav2",
        display_name="WMA",
        description="Windows Media Audio",
    ),
    "alac": CodecInfo(
        codec_name="alac",
        display_name="ALAC",
        description="Apple 无损音频编码",
    ),
}

# -- Containers ------------------------------------------------------------

CONTAINERS: dict[str, ContainerInfo] = {
    # Video containers
    "mp4": ContainerInfo(
        name="MP4",
        extension="mp4",
        description="MPEG-4 Part 14，兼容性最广",
        compatible_video_codecs=["libx264", "libx265"],
        compatible_audio_codecs=["aac", "libmp3lame", "ac3"],
        default_video_codec="libx264",
        default_audio_codec="aac",
    ),
    "mkv": ContainerInfo(
        name="MKV",
        extension="mkv",
        description="Matroska，支持几乎所有编码",
        compatible_video_codecs=["libx264", "libx265", "libvpx-vp9", "libaom-av1"],
        compatible_audio_codecs=["aac", "libmp3lame", "flac", "libopus", "libvorbis", "ac3"],
        default_video_codec="libx264",
        default_audio_codec="aac",
    ),
    "avi": ContainerInfo(
        name="AVI",
        extension="avi",
        description="传统微软容器格式",
        compatible_video_codecs=["libx264", "mpeg4"],
        compatible_audio_codecs=["libmp3lame", "pcm_s16le", "ac3"],
        default_video_codec="libx264",
        default_audio_codec="libmp3lame",
    ),
    "mov": ContainerInfo(
        name="MOV",
        extension="mov",
        description="Apple QuickTime 容器",
        compatible_video_codecs=["libx264", "libx265", "prores_ks"],
        compatible_audio_codecs=["aac", "pcm_s16le", "ac3"],
        default_video_codec="libx264",
        default_audio_codec="aac",
    ),
    "flv": ContainerInfo(
        name="FLV",
        extension="flv",
        description="Flash 视频，Web 流媒体",
        compatible_video_codecs=["libx264"],
        compatible_audio_codecs=["aac", "libmp3lame"],
        default_video_codec="libx264",
        default_audio_codec="aac",
    ),
    "wmv": ContainerInfo(
        name="WMV",
        extension="wmv",
        description="Windows Media Video",
        compatible_video_codecs=["wmv2"],
        compatible_audio_codecs=["wmav2"],
        default_video_codec="wmv2",
        default_audio_codec="wmav2",
    ),
    "webm": ContainerInfo(
        name="WEBM",
        extension="webm",
        description="开放 Web 格式",
        compatible_video_codecs=["libvpx", "libvpx-vp9", "libaom-av1"],
        compatible_audio_codecs=["libopus", "libvorbis"],
        default_video_codec="libvpx-vp9",
        default_audio_codec="libopus",
    ),
    # Audio-only containers
    "mp3": ContainerInfo(
        name="MP3",
        extension="mp3",
        description="最常见的音频格式",
        is_audio_only=True,
        compatible_audio_codecs=["libmp3lame"],
        default_audio_codec="libmp3lame",
    ),
    "wav": ContainerInfo(
        name="WAV",
        extension="wav",
        description="未压缩无损音频",
        is_audio_only=True,
        compatible_audio_codecs=["pcm_s16le"],
        default_audio_codec="pcm_s16le",
    ),
    "aac": ContainerInfo(
        name="AAC",
        extension="aac",
        description="高质量有损音频",
        is_audio_only=True,
        compatible_audio_codecs=["aac"],
        default_audio_codec="aac",
    ),
    "flac": ContainerInfo(
        name="FLAC",
        extension="flac",
        description="无损音频压缩",
        is_audio_only=True,
        compatible_audio_codecs=["flac"],
        default_audio_codec="flac",
    ),
    "ogg": ContainerInfo(
        name="OGG",
        extension="ogg",
        description="开源音频容器",
        is_audio_only=True,
        compatible_audio_codecs=["libvorbis", "libopus"],
        default_audio_codec="libvorbis",
    ),
    "m4a": ContainerInfo(
        name="M4A",
        extension="m4a",
        description="MP4 音频容器",
        is_audio_only=True,
        compatible_audio_codecs=["aac", "alac"],
        default_audio_codec="aac",
    ),
}
