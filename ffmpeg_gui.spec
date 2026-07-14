# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for building the FFmpeg GUI as a standalone app."""

import os
import platform

app_version = os.environ.get("APP_VERSION", "0.1.0")

# 确定当前平台的 FFmpeg 资源目录
system = platform.system().lower()
machine = platform.machine().lower()

if system == "darwin":
    platform_dir = "darwin-arm64" if machine == "arm64" else "darwin-x86_64"
elif system == "windows":
    platform_dir = "win64"
else:  # linux
    platform_dir = "linux-arm64" if machine == "aarch64" else "linux-x86_64"

# 内置 FFmpeg 二进制文件（使用绝对路径并验证存在性）
spec_dir = os.path.dirname(os.path.abspath(SPEC))
ffmpeg_src_dir = os.path.join(spec_dir, "src", "ffmpeg_tui", "resources", "ffmpeg", platform_dir)

# 验证 FFmpeg 文件存在
ffmpeg_binary = "ffmpeg.exe" if system == "windows" else "ffmpeg"
ffmpeg_binary_path = os.path.join(ffmpeg_src_dir, ffmpeg_binary)

if not os.path.isfile(ffmpeg_binary_path):
    raise FileNotFoundError(
        f"FFmpeg 二进制文件不存在: {ffmpeg_binary_path}\n"
        f"请先运行: python scripts/download_ffmpeg_binaries.py"
    )

print(f"✓ 找到 FFmpeg: {ffmpeg_binary_path} ({os.path.getsize(ffmpeg_binary_path) / 1024 / 1024:.1f} MB)")

ffmpeg_resources = [
    (
        ffmpeg_src_dir,
        f"ffmpeg_tui/resources/ffmpeg/{platform_dir}",
    ),
]

a = Analysis(
    ["src/ffmpeg_tui/gui/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=ffmpeg_resources,
    hiddenimports=[
        "ffmpeg_tui.core",
        "ffmpeg_tui.models",
        "ffmpeg_tui.utils",
        "ffmpeg_tui.gui",
        "ffmpeg_tui.gui.tabs",
        "ffmpeg_tui.gui.widgets",
        "pydantic",
        "pydantic.dataclasses",
        "pydantic_core",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "textual",
        "rich",
        "pytest",
        "black",
        "ruff",
        "mypy",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FFmpegTools",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

# macOS: create .app bundle
if platform.system() == "Darwin":
    app = BUNDLE(
        exe,
        name="FFmpegTools.app",
        icon=None,
        bundle_identifier="com.ffmpegTui.gui",
        info_plist={
            "CFBundleShortVersionString": app_version,
            "NSHighResolutionCapable": True,
        },
    )
