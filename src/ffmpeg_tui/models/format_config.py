"""Format configuration models for video and audio formats."""

from enum import Enum

from pydantic import BaseModel


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
