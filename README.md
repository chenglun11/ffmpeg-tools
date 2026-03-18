# FFmpeg Tools

一个简洁易用的 FFmpeg 图形界面工具，支持视频/音频格式转换、压缩和 WhatsApp 媒体优化。

## 功能特性

- **格式转换** - 支持主流视频/音频格式互转（MP4, MKV, AVI, MOV, MP3, AAC, FLAC 等）
- **视频压缩** - 自定义分辨率、码率、帧率和编码预设，智能预估输出大小
- **Meta 专版** - 针对 WhatsApp Business API 优化的媒体转换（16MB 视频/音频，5MB 图片）
- **自动更新检测** - 启动时自动检查新版本
- **FFmpeg 管理** - 内置 FFmpeg 下载安装功能

## 下载安装

从 [Releases](https://github.com/chenglun11/ffmpeg-tools/releases) 下载对应平台的版本：

- **macOS (Apple Silicon)**: `FFmpegTools-macos-arm64.zip`
- **Windows (x64)**: `FFmpegTools-windows-x86_64.zip`
- **Linux (x64)**: `FFmpegTools-linux-x86_64.tar.gz`

### macOS
解压后双击 `FFmpegTools.app` 运行。首次打开可能需要在"系统设置 → 隐私与安全性"中允许。

### Windows
解压后双击 `FFmpegTools.exe` 运行。

### Linux
```bash
tar -xzf FFmpegTools-linux-x86_64.tar.gz
./FFmpegTools
```

## 开发

### 环境要求
- Python 3.10+
- PyQt6

### 安装依赖
```bash
pip install -e ".[gui,dev]"
```

### 运行
```bash
python -m ffmpeg_tui.gui
```

### 打包
```bash
pyinstaller ffmpeg_gui.spec --noconfirm
```

## 技术栈

- **GUI**: PyQt6
- **FFmpeg**: 通过 subprocess 调用
- **打包**: PyInstaller
- **CI/CD**: GitHub Actions

## License

MIT
