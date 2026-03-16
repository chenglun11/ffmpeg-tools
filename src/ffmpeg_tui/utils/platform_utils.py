import platform
from pathlib import Path
from platformdirs import user_data_dir, user_config_dir, user_log_dir

APP_NAME = "ffmpeg-tui"

def get_platform() -> str:
    """返回当前平台标识: 'windows', 'macos', 'linux'"""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system

def get_arch() -> str:
    """返回 CPU 架构: 'x86_64', 'arm64'"""
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x86_64"
    if machine in ("arm64", "aarch64"):
        return "arm64"
    return machine

FFMPEG_DOWNLOAD_URLS = {
    ("windows", "x86_64"): "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    ("windows", "arm64"): "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    ("linux", "x86_64"): "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
    ("linux", "arm64"): "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz",
    ("macos", "x86_64"): "https://evermeet.cx/ffmpeg/getrelease",
    ("macos", "arm64"): "https://evermeet.cx/ffmpeg/getrelease",
}

def get_download_url(plat: str | None = None, arch: str | None = None) -> str:
    """返回 FFmpeg 下载 URL"""
    plat = plat or get_platform()
    arch = arch or get_arch()
    url = FFMPEG_DOWNLOAD_URLS.get((plat, arch))
    if not url:
        raise ValueError(f"不支持的平台/架构组合: {plat}/{arch}")
    return url

def get_data_dir() -> Path:
    """获取应用数据目录"""
    path = Path(user_data_dir(APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_config_dir() -> Path:
    """获取配置目录"""
    path = Path(user_config_dir(APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_log_dir() -> Path:
    """获取日志目录"""
    path = Path(user_log_dir(APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path
