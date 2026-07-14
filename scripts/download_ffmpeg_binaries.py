#!/usr/bin/env python3
"""下载各平台的 FFmpeg 静态编译二进制文件到资源目录。"""

import asyncio
import shutil
import tarfile
import zipfile
from pathlib import Path

import httpx

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
RESOURCES_DIR = PROJECT_ROOT / "src" / "ffmpeg_tui" / "resources" / "ffmpeg"

# 各平台的下载 URL
DOWNLOAD_URLS = {
    "darwin-arm64": "https://www.osxexperts.net/ffmpeg7arm.zip",
    "darwin-x86_64": "https://www.osxexperts.net/ffmpeg7intel.zip",
    "win64": (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
        "ffmpeg-master-latest-win64-gpl.zip"
    ),
    "linux-x86_64": (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
        "ffmpeg-master-latest-linux64-gpl.tar.xz"
    ),
    "linux-arm64": (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
        "ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
    ),
}


async def download_file(url: str, dest: Path) -> None:
    """下载文件到指定路径。"""
    print(f"  下载中: {url}")
    async with httpx.AsyncClient(follow_redirects=True, timeout=600) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            with open(dest, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        percent = (downloaded / total) * 100
                        print(f"\r  进度: {percent:.1f}%", end="", flush=True)
            print()


def extract_binaries(archive_path: Path, platform_dir: Path) -> None:
    """从压缩包中提取 ffmpeg 和 ffprobe 二进制文件。"""
    print(f"  提取二进制文件...")
    temp_dir = platform_dir / "_temp"
    temp_dir.mkdir(exist_ok=True)

    try:
        # 解压
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(temp_dir)
        elif archive_path.name.endswith(".tar.xz"):
            with tarfile.open(archive_path, "r:xz") as tf:
                tf.extractall(temp_dir)

        # 查找二进制文件
        exe_suffix = ".exe" if "win" in platform_dir.name else ""
        ffmpeg_name = f"ffmpeg{exe_suffix}"
        ffprobe_name = f"ffprobe{exe_suffix}"

        found_ffmpeg = None
        found_ffprobe = None

        for p in temp_dir.rglob(ffmpeg_name):
            if p.is_file():
                found_ffmpeg = p
                break

        for p in temp_dir.rglob(ffprobe_name):
            if p.is_file():
                found_ffprobe = p
                break

        if found_ffmpeg is None:
            raise RuntimeError(f"未找到 {ffmpeg_name}")

        # 复制到目标目录
        dest_ffmpeg = platform_dir / ffmpeg_name
        shutil.copy2(found_ffmpeg, dest_ffmpeg)
        print(f"  ✓ 复制: {dest_ffmpeg.name}")

        if found_ffprobe:
            dest_ffprobe = platform_dir / ffprobe_name
            shutil.copy2(found_ffprobe, dest_ffprobe)
            print(f"  ✓ 复制: {dest_ffprobe.name}")

        # 设置可执行权限（非 Windows）
        if exe_suffix == "":
            dest_ffmpeg.chmod(0o755)
            if found_ffprobe:
                dest_ffprobe.chmod(0o755)

    finally:
        # 清理临时文件
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


async def download_platform(platform: str, url: str) -> None:
    """下载并提取指定平台的 FFmpeg。"""
    print(f"\n[{platform}]")
    platform_dir = RESOURCES_DIR / platform
    platform_dir.mkdir(parents=True, exist_ok=True)

    # 确定压缩包文件名
    archive_name = url.rsplit("/", 1)[-1]
    archive_path = platform_dir / archive_name

    # 下载
    await download_file(url, archive_path)

    # 提取
    extract_binaries(archive_path, platform_dir)

    # 删除压缩包
    archive_path.unlink()
    print(f"  ✓ 完成")


async def main() -> None:
    """主函数：下载所有平台的 FFmpeg。"""
    print("=" * 60)
    print("下载 FFmpeg 静态编译二进制文件")
    print("=" * 60)
    print(f"目标目录: {RESOURCES_DIR}")

    for platform, url in DOWNLOAD_URLS.items():
        try:
            await download_platform(platform, url)
        except Exception as e:
            print(f"  ✗ 错误: {e}")

    print("\n" + "=" * 60)
    print("全部完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
