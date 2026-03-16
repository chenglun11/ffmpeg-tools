# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for building the FFmpeg GUI as a standalone app."""

import os
import platform

block_cipher = None
app_version = os.environ.get("APP_VERSION", "0.1.0")

a = Analysis(
    ["src/ffmpeg_tui/gui/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=[
        "ffmpeg_tui.core",
        "ffmpeg_tui.models",
        "ffmpeg_tui.utils",
        "ffmpeg_tui.gui",
        "ffmpeg_tui.gui.tabs",
        "ffmpeg_tui.gui.widgets",
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
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

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
        bundle_identifier="com.ffmpeg-tui.gui",
        info_plist={
            "CFBundleShortVersionString": app_version,
            "NSHighResolutionCapable": True,
        },
    )
