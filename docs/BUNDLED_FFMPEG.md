# 内置 FFmpeg 说明

## 概述

从 v0.4.0 开始，FFmpeg Tools 应用程序已内置 FFmpeg 二进制文件，用户无需手动下载或安装 FFmpeg 即可直接使用所有功能。

## 特性

### ✅ 开箱即用
- 应用启动后自动检测并使用内置的 FFmpeg
- 无需额外配置，所有转换和压缩功能立即可用
- 状态栏显示 "FFmpeg: ... (内置)"

### 🎯 智能检测顺序
应用程序按以下优先级查找 FFmpeg：
1. **内置版本**（应用资源目录）- 最高优先级
2. 本地下载版本（用户数据目录）
3. 系统 PATH 中的版本

### 🌍 多平台支持
内置 FFmpeg 支持以下平台：
- macOS ARM64 (Apple Silicon)
- macOS x86_64 (Intel)
- Windows x64
- Linux x86_64
- Linux ARM64

## 技术实现

### 资源目录结构
```
src/ffmpeg_tui/resources/ffmpeg/
├── darwin-arm64/
│   └── ffmpeg
├── darwin-x86_64/
│   └── ffmpeg
├── linux-x86_64/
│   ├── ffmpeg
│   └── ffprobe
├── linux-arm64/
│   ├── ffmpeg
│   └── ffprobe
└── win64/
    ├── ffmpeg.exe
    └── ffprobe.exe
```

### 检测逻辑
参见 `src/ffmpeg_tui/core/ffmpeg_manager.py` 中的 `_get_bundled_ffmpeg_path()` 函数：

```python
def _get_bundled_ffmpeg_path() -> Optional[Path]:
    """返回内置的 FFmpeg 二进制文件路径（如果存在）。"""
    # 1. 确定当前平台
    # 2. 处理 PyInstaller 打包后的路径
    # 3. 返回对应平台的 FFmpeg 路径
```

### 打包配置
PyInstaller 配置（`ffmpeg_gui.spec`）会自动包含对应平台的 FFmpeg 二进制文件：

```python
ffmpeg_resources = [
    (
        f"src/ffmpeg_tui/resources/ffmpeg/{platform_dir}",
        f"ffmpeg_tui/resources/ffmpeg/{platform_dir}",
    ),
]
```

## 应用体积

内置 FFmpeg 后的应用体积（单个平台打包）：
- macOS ARM64: ~90 MB
- macOS x86_64: ~120 MB
- Windows: ~180 MB
- Linux x86_64: ~180 MB
- Linux ARM64: ~150 MB

> 注：体积增加主要来自 FFmpeg 静态编译二进制文件（包含完整的编解码器支持）

## 开发说明

### 下载 FFmpeg 二进制文件

如果需要重新下载或更新 FFmpeg 二进制文件：

```bash
python scripts/download_ffmpeg_binaries.py
```

这会自动下载所有平台的 FFmpeg 并提取到正确的目录。

### Git 配置

由于 FFmpeg 二进制文件体积较大（总计约 500 MB），建议：
- **方案 A**：不提交到 git，仅在打包构建时下载
- **方案 B**：使用 Git LFS 管理二进制文件
- **方案 C**：提交到 git（会增加仓库大小）

当前配置：二进制文件**未被**添加到 `.gitignore`，可根据实际需求调整。

### 打包构建

构建包含内置 FFmpeg 的应用：

```bash
# 确保 FFmpeg 二进制文件已下载
python scripts/download_ffmpeg_binaries.py

# 使用 PyInstaller 打包
pyinstaller ffmpeg_gui.spec
```

生成的应用会自动包含对应平台的 FFmpeg。

## 用户体验改进

### 设置页面
- ✅ 显示 "已安装 (内置版本)" 状态
- ✅ 隐藏 "下载安装 FFmpeg" 按钮（内置版本时）
- ✅ 显示 FFmpeg 路径和版本信息

### 主界面
- ✅ 状态栏显示 "FFmpeg: ... (内置)"
- ✅ 所有功能按钮默认启用
- ✅ 无需任何手动配置

### 错误处理
如果内置 FFmpeg 无法正常工作（极少见情况）：
1. 应用会自动尝试检测系统 PATH 中的 FFmpeg
2. 用户可以在设置页面手动下载独立版本
3. 可以查看详细路径和版本信息用于排查

## FAQ

**Q: 为什么要内置 FFmpeg？**  
A: 大量用户反馈不会下载和安装 FFmpeg，内置后可以开箱即用，大幅提升用户体验。

**Q: 内置的 FFmpeg 是否完整？**  
A: 是的，使用的是官方静态编译的完整版本，包含 GPL 编解码器支持。

**Q: 可以使用自己的 FFmpeg 吗？**  
A: 可以。如果系统 PATH 中有 FFmpeg，或在用户数据目录下载了独立版本，应用会优先使用内置版本，但仍然保留其他检测路径。

**Q: 应用体积为什么这么大？**  
A: FFmpeg 是一个功能完整的多媒体处理框架，静态编译版本包含了数百种编解码器，体积在 50-140 MB 之间（因平台而异）。

**Q: 会自动更新 FFmpeg 吗？**  
A: 内置的 FFmpeg 版本随应用更新而更新。用户也可以在设置页面手动下载最新的独立版本。

## 授权说明

- FFmpeg 使用 **GPL v2.0** 许可证
- 静态编译版本包含 GPL 编解码器
- 本应用使用 **MIT** 许可证
- 两者兼容，但需注意：分发包含 FFmpeg 的应用时需遵守 GPL 条款

## 相关链接

- [FFmpeg 官方网站](https://ffmpeg.org/)
- [FFmpeg Builds (Windows/Linux)](https://github.com/BtbN/FFmpeg-Builds)
- [OSX Experts FFmpeg (macOS)](https://www.osxexperts.net/)
