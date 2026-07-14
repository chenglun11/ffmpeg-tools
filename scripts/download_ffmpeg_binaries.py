#!/usr/bin/env python3
"""下载各平台的 FFmpeg 静态编译二进制文件到资源目录。

用法：
    python scripts/download_ffmpeg_binaries.py            # 只下载当前平台
    python scripts/download_ffmpeg_binaries.py --all      # 下载所有平台
    python scripts/download_ffmpeg_binaries.py win64      # 下载指定平台

失败时以非零退出码结束，便于 CI 检测。
"""

import argparse
import platform
import shutil
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

# Windows 控制台默认 cp1252 编码，无法输出中文，强制切到 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
RESOURCES_DIR = PROJECT_ROOT / "src" / "ffmpeg_tui" / "resources" / "ffmpeg"

# 各平台的下载 URL
# macOS 用 osxexperts.net（arm/intel 原生构建，文件名干净的 .zip）
# Windows/Linux 用 BtbN/FFmpeg-Builds（含 ffmpeg + ffprobe 的 bundle）
DOWNLOAD_URLS = {
    "darwin-arm64": {
        "ffmpeg": "https://www.osxexperts.net/ffmpeg7arm.zip",
    },
    "darwin-x86_64": {
        "ffmpeg": "https://www.osxexperts.net/ffmpeg7intel.zip",
    },
    "win64": {
        "bundle": (
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
            "ffmpeg-master-latest-win64-gpl.zip"
        ),
    },
    "linux-x86_64": {
        "bundle": (
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
            "ffmpeg-master-latest-linux64-gpl.tar.xz"
        ),
    },
    "linux-arm64": {
        "bundle": (
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
            "ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
        ),
    },
}


def current_platform() -> str:
    """返回当前运行平台的标识符。"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        return "darwin-arm64" if machine == "arm64" else "darwin-x86_64"
    elif system == "windows":
        return "win64"
    elif system == "linux":
        return "linux-arm64" if machine in ("aarch64", "arm64") else "linux-x86_64"
    raise RuntimeError(f"不支持的平台: {system} {machine}")


def download_file(url: str, dest: Path) -> None:
    """下载文件到指定路径（使用标准库，无需第三方依赖）。"""
    print(f"  下载中: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=600) as response:
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    percent = (downloaded / total) * 100
                    print(f"\r  进度: {percent:.1f}%", end="", flush=True)
    print()


def extract_binaries(archive_path: Path, platform_dir: Path) -> list[str]:
    """从压缩包中提取 ffmpeg 和 ffprobe 二进制文件。

    Returns:
        成功提取的文件名列表。
    """
    print(f"  提取二进制文件...")
    temp_dir = platform_dir / "_temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(exist_ok=True)

    extracted: list[str] = []
    try:
        # 解压
        if archive_path.name.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(temp_dir)
        elif archive_path.name.endswith(".tar.xz"):
            with tarfile.open(archive_path, "r:xz") as tf:
                tf.extractall(temp_dir)
        else:
            raise RuntimeError(f"未知压缩格式: {archive_path.name}")

        # 查找二进制文件
        exe_suffix = ".exe" if platform_dir.name.startswith("win") else ""

        for name in (f"ffmpeg{exe_suffix}", f"ffprobe{exe_suffix}"):
            found = None
            # 跳过 macOS 解压产生的 __MACOSX 目录
            for p in temp_dir.rglob(name):
                if p.is_file() and "__MACOSX" not in p.parts:
                    found = p
                    break

            if found is not None:
                dest = platform_dir / name
                shutil.copy2(found, dest)
                if exe_suffix == "":
                    dest.chmod(0o755)
                extracted.append(name)
                print(f"  ✓ 提取: {name}")

        return extracted

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def download_platform(plat: str) -> None:
    """下载并提取指定平台的 FFmpeg。失败时抛出异常。"""
    print(f"\n[{plat}]")
    if plat not in DOWNLOAD_URLS:
        raise RuntimeError(f"未知平台: {plat}")

    platform_dir = RESOURCES_DIR / plat
    platform_dir.mkdir(parents=True, exist_ok=True)

    all_extracted: list[str] = []
    for url in DOWNLOAD_URLS[plat].values():
        archive_name = url.rsplit("/", 1)[-1]
        archive_path = platform_dir / archive_name

        download_file(url, archive_path)
        try:
            all_extracted += extract_binaries(archive_path, platform_dir)
        finally:
            archive_path.unlink(missing_ok=True)

    # 校验：至少要有 ffmpeg
    exe_suffix = ".exe" if plat.startswith("win") else ""
    ffmpeg_name = f"ffmpeg{exe_suffix}"
    if ffmpeg_name not in all_extracted:
        raise RuntimeError(f"{plat}: 未能提取 {ffmpeg_name}")

    print(f"  ✓ 完成 ({', '.join(all_extracted)})")


def main() -> int:
    parser = argparse.ArgumentParser(description="下载 FFmpeg 二进制文件")
    parser.add_argument(
        "platform",
        nargs="?",
        help="指定平台（如 win64、darwin-arm64）。默认只下载当前平台",
    )
    parser.add_argument(
        "--all", action="store_true", help="下载所有平台（用于本地全量打包）"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("下载 FFmpeg 静态编译二进制文件")
    print("=" * 60)
    print(f"目标目录: {RESOURCES_DIR}")

    if args.all:
        targets = list(DOWNLOAD_URLS.keys())
    elif args.platform:
        targets = [args.platform]
    else:
        targets = [current_platform()]

    print(f"目标平台: {', '.join(targets)}")

    failed: list[str] = []
    for plat in targets:
        try:
            download_platform(plat)
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            failed.append(plat)

    print("\n" + "=" * 60)
    if failed:
        print(f"失败的平台: {', '.join(failed)}")
        print("=" * 60)
        return 1

    print("全部完成！")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
