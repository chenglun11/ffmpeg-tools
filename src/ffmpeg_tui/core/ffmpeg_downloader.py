"""自动下载和安装 FFmpeg 的工具。"""

import platform
import tarfile
import zipfile
from pathlib import Path
from typing import Callable, Optional

import httpx

from ffmpeg_tui.config import FFMPEG_DIR

# FFmpeg 7.0 下载链接（官方构建）
FFMPEG_DOWNLOADS = {
    "darwin-arm64": {
        "url": "https://evermeet.cx/ffmpeg/ffmpeg-7.0.zip",
        "type": "zip",
    },
    "darwin-x86_64": {
        "url": "https://evermeet.cx/ffmpeg/ffmpeg-7.0.zip",
        "type": "zip",
    },
    "windows": {
        "url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        "type": "zip",
    },
    "linux-x86_64": {
        "url": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
        "type": "tar.xz",
    },
    "linux-arm64": {
        "url": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz",
        "type": "tar.xz",
    },
}


def get_platform_key() -> Optional[str]:
    """获取当前平台的标识符。"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        return "darwin-arm64" if machine == "arm64" else "darwin-x86_64"
    elif system == "windows":
        return "windows"
    elif system == "linux":
        return "linux-arm64" if machine in ("aarch64", "arm64") else "linux-x86_64"
    return None


async def download_ffmpeg(
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> bool:
    """
    下载并安装 FFmpeg。

    Args:
        progress_callback: 进度回调函数 (progress: int, message: str)

    Returns:
        bool: 是否成功
    """
    platform_key = get_platform_key()
    if not platform_key or platform_key not in FFMPEG_DOWNLOADS:
        if progress_callback:
            progress_callback(0, f"不支持的平台: {platform.system()} {platform.machine()}")
        return False

    download_info = FFMPEG_DOWNLOADS[platform_key]
    url = download_info["url"]
    archive_type = download_info["type"]

    # 创建目录
    FFMPEG_DIR.mkdir(parents=True, exist_ok=True)
    bin_dir = FFMPEG_DIR / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    # 下载文件
    archive_path = FFMPEG_DIR / f"ffmpeg.{archive_type}"

    try:
        if progress_callback:
            progress_callback(5, "开始下载 FFmpeg...")

        async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()

                total = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(archive_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total > 0 and progress_callback:
                            progress = 5 + int((downloaded / total) * 60)
                            mb_downloaded = downloaded / (1024 * 1024)
                            mb_total = total / (1024 * 1024)
                            progress_callback(
                                progress,
                                f"下载中: {mb_downloaded:.1f} MB / {mb_total:.1f} MB",
                            )

        if progress_callback:
            progress_callback(70, "下载完成，正在解压...")

        # 解压文件
        if archive_type == "zip":
            _extract_zip(archive_path, bin_dir, progress_callback)
        elif archive_type == "tar.xz":
            _extract_tar(archive_path, bin_dir, progress_callback)

        if progress_callback:
            progress_callback(95, "清理临时文件...")

        # 删除压缩包
        archive_path.unlink(missing_ok=True)

        if progress_callback:
            progress_callback(100, "安装完成！")

        return True

    except Exception as e:
        if progress_callback:
            progress_callback(0, f"安装失败: {str(e)}")
        # 清理失败的下载
        archive_path.unlink(missing_ok=True)
        return False


def _extract_zip(
    archive_path: Path,
    target_dir: Path,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> None:
    """解压 ZIP 文件并提取 FFmpeg 可执行文件。"""
    with zipfile.ZipFile(archive_path, "r") as zf:
        # 查找 ffmpeg 和 ffprobe 可执行文件
        exe_suffix = ".exe" if platform.system() == "Windows" else ""
        ffmpeg_names = [f"ffmpeg{exe_suffix}", f"ffprobe{exe_suffix}"]

        for member in zf.namelist():
            basename = Path(member).name
            if basename in ffmpeg_names:
                # 提取到目标目录
                source = zf.open(member)
                target = target_dir / basename
                with open(target, "wb") as f:
                    f.write(source.read())
                # 添加执行权限（Unix 系统）
                if platform.system() != "Windows":
                    target.chmod(0o755)

                if progress_callback:
                    progress_callback(80, f"已提取: {basename}")


def _extract_tar(
    archive_path: Path,
    target_dir: Path,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> None:
    """解压 tar.xz 文件并提取 FFmpeg 可执行文件。"""
    with tarfile.open(archive_path, "r:xz") as tf:
        ffmpeg_names = ["ffmpeg", "ffprobe"]

        for member in tf.getmembers():
            basename = Path(member.name).name
            if basename in ffmpeg_names:
                # 提取文件
                source = tf.extractfile(member)
                if source:
                    target = target_dir / basename
                    with open(target, "wb") as f:
                        f.write(source.read())
                    # 添加执行权限
                    target.chmod(0o755)

                    if progress_callback:
                        progress_callback(80, f"已提取: {basename}")
