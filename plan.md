# FFmpeg TUI 工具项目实施计划

## 项目概述

**项目名称**: FFmpeg TUI Tools
**目标**: 创建一个基于 Python 的 TUI（文本用户界面）工具，用于简化 FFmpeg 的视频/音频格式转换操作
**技术栈**: Python 3.8+, Textual, FFmpeg
**目标平台**: Windows 10+, macOS 10.15+, Linux（主流发行版）

## 技术研究总结

### 1. Textual 框架架构模式

基于对 [Textual 官方文档](https://textual.textualize.io/)和[最佳实践](https://www.mlhive.com/2026/01/building-modern-terminal-apps-with-python-and-textual)的研究，Textual 提供了以下核心特性：

- **响应式状态管理**: 使用 `reactive` 属性自动触发 UI 更新
- **组件化架构**: 通过 `Widget` 和 `Screen` 构建模块化界面
- **事件驱动模型**: 基于消息传递的事件处理机制
- **CSS 样式系统**: 类似 Web 的样式定义方式
- **异步优先**: 基于 asyncio 的异步架构

**关键架构模式**:
- Screen-based navigation（多屏幕导航）
- Modal dialogs（模态对话框）
- Custom widgets with reactive properties（自定义响应式组件）
- Message passing for component communication（组件间消息传递）

### 2. FFmpeg 自动安装方案

研究了多个 Python 包和下载源：

**现有 Python 包**:
- [ffmpeg-downloader](https://pypi.org/project/ffmpeg-downloader/): 自动下载最新 FFmpeg 预编译二进制文件
- [dlffmpeg](https://pypi.org/project/dlffmpeg/): 简单的下载和安装脚本
- [local-ffmpeg](https://pypi.org/project/local-ffmpeg/): 自动处理平台特定安装

**官方下载源**:
- **Windows**: [gyan.dev](https://www.gyan.dev/) - 提供 GPL 和 Essentials 构建版本
- **Windows/Linux**: [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases) - 自动化构建系统，每日更新
- **macOS**: Homebrew 或静态二进制文件
- **Linux**: 系统包管理器（apt, yum, pacman）或静态二进制文件

**推荐方案**:
1. 优先检测系统已安装的 FFmpeg
2. 如未安装，根据平台自动下载静态二进制文件：
   - Windows: 从 gyan.dev 或 BtbN 下载
   - macOS: 提示使用 Homebrew 或下载静态二进制
   - Linux: 提示使用包管理器或下载静态二进制

### 3. FFmpeg 进度解析

基于 [Stack Overflow 讨论](https://stackoverflow.com/questions/7632589/getting-realtime-output-from-ffmpeg-to-be-used-in-progress-bar-pyqt4-stdout)和相关包研究：

- 使用 `-progress pipe:1` 参数将进度输出到 stdout
- 解析输出中的 `frame=`, `time=`, `speed=` 等关键信息
- 可用的辅助包：
  - [ffmpeg-progress](https://pypi.org/project/ffmpeg-progress/)
  - [better-ffmpeg-progress](https://pypi.org/project/better-ffmpeg-progress/)

### 4. 项目结构最佳实践

参考 [2025 Python 最佳实践](https://nerdleveltech.com/python-best-practices-the-2025-guide-for-clean-fast-and-secure-code)和[模块化设计](https://labex.io/tutorials/python-how-to-design-modular-python-projects-420186)：

- 使用 `pyproject.toml` 进行项目配置
- 采用清晰的模块化架构（按功能而非类型组织）
- 使用 Poetry 或 setuptools 进行依赖管理
- 遵循 Clean Architecture 原则

## 项目架构设计

### 目录结构

```
ffmpeg_imp_tools/
├── pyproject.toml              # 项目配置和依赖
├── README.md                   # 项目说明
├── LICENSE                     # 许可证
├── .gitignore                  # Git 忽略文件
├── src/
│   └── ffmpeg_tui/
│       ├── __init__.py
│       ├── __main__.py         # 入口点
│       ├── app.py              # 主应用类
│       ├── config.py           # 配置管理
│       │
│       ├── core/               # 核心业务逻辑
│       │   ├── __init__.py
│       │   ├── ffmpeg_manager.py    # FFmpeg 检测/安装/管理
│       │   ├── ffmpeg_executor.py   # FFmpeg 命令执行
│       │   ├── command_builder.py   # FFmpeg 命令构建
│       │   └── progress_parser.py   # 进度解析
│       │
│       ├── ui/                 # UI 组件
│       │   ├── __init__.py
│       │   ├── screens/        # 屏幕
│       │   │   ├── __init__.py
│       │   │   ├── main_screen.py
│       │   │   ├── convert_screen.py
│       │   │   ├── compress_screen.py
│       │   │   └── settings_screen.py
│       │   │
│       │   ├── widgets/        # 自定义组件
│       │   │   ├── __init__.py
│       │   │   ├── file_picker.py
│       │   │   ├── progress_display.py
│       │   │   ├── format_selector.py
│       │   │   └── parameter_panel.py
│       │   │
│       │   └── styles/         # CSS 样式
│       │       ├── __init__.py
│       │       └── main.tcss
│       │
│       ├── models/             # 数据模型
│       │   ├── __init__.py
│       │   ├── conversion_task.py
│       │   ├── format_config.py
│       │   └── ffmpeg_info.py
│       │
│       └── utils/              # 工具函数
│           ├── __init__.py
│           ├── file_utils.py
│           ├── platform_utils.py
│           ├── logger.py
│           └── validators.py
│
├── tests/                      # 测试
│   ├── __init__.py
│   ├── test_core/
│   ├── test_ui/
│   └── test_utils/
│
└── docs/                       # 文档
    ├── user_guide.md
    └── development.md
```

### 核心模块设计

#### 1. FFmpeg Manager（FFmpeg 管理器）

**职责**:
- 检测系统中的 FFmpeg 安装
- 自动下载和安装 FFmpeg
- 验证 FFmpeg 版本和功能

**关键方法**:
```python
class FFmpegManager:
    def check_installation() -> bool
    def get_version() -> str
    def download_ffmpeg(platform: str) -> Path
    def install_ffmpeg(binary_path: Path) -> bool
    def get_ffmpeg_path() -> Path
```

#### 2. Command Builder（命令构建器）

**职责**:
- 根据用户参数构建 FFmpeg 命令
- 支持格式转换、压缩等操作
- 参数验证和优化

**关键方法**:
```python
class CommandBuilder:
    def build_convert_command(input_file, output_file, format) -> List[str]
    def build_compress_command(input_file, output_file, params) -> List[str]
    def add_video_params(resolution, bitrate, framerate) -> Self
    def add_audio_params(codec, bitrate) -> Self
```

#### 3. FFmpeg Executor（执行器）

**职责**:
- 执行 FFmpeg 命令
- 实时解析进度输出
- 错误处理和日志记录

**关键方法**:
```python
class FFmpegExecutor:
    async def execute(command: List[str], progress_callback) -> bool
    def parse_progress(output: str) -> ProgressInfo
    def cancel_execution() -> None
```

#### 4. UI Screens（界面屏幕）

**主要屏幕**:
- **MainScreen**: 主菜单（选择操作类型）
- **ConvertScreen**: 格式转换界面
- **CompressScreen**: 视频压缩界面
- **SettingsScreen**: 设置界面（FFmpeg 路径、默认参数等）

#### 5. Custom Widgets（自定义组件）

**核心组件**:
- **FilePicker**: 文件选择器（基于 DirectoryTree）
- **ProgressDisplay**: 进度显示（进度条 + 详细信息）
- **FormatSelector**: 格式选择器（下拉列表）
- **ParameterPanel**: 参数配置面板（分辨率、码率、帧率等）

## 详细实施计划

### 阶段 1: 项目初始化（1-2 天）

**任务**:
1. 创建项目目录结构
2. 配置 `pyproject.toml`
   - 项目元数据
   - 依赖项：textual, rich, httpx, platformdirs
   - 开发依赖：pytest, black, ruff, mypy
3. 设置 Git 仓库和 `.gitignore`
4. 创建基础 README 和 LICENSE
5. 初始化日志系统

**依赖**: 无
**可并行**: 否

### 阶段 2: FFmpeg 管理模块（3-4 天）

**任务**:
1. 实现 `FFmpegManager` 类
   - 检测系统 FFmpeg 安装
   - 获取版本信息
   - 验证功能支持
2. 实现跨平台下载逻辑
   - Windows: 从 gyan.dev 或 BtbN 下载
   - macOS: 检测 Homebrew，提供安装指引
   - Linux: 检测包管理器，提供安装指引
3. 实现二进制文件管理
   - 下载进度显示
   - 文件验证（校验和）
   - 安装到用户目录
4. 编写单元测试

**依赖**: 阶段 1
**可并行**: 部分（下载逻辑可与检测逻辑并行开发）

### 阶段 3: FFmpeg 命令构建和执行（3-4 天）

**任务**:
1. 实现 `CommandBuilder` 类
   - 格式转换命令构建
   - 视频压缩命令构建
   - 参数验证和优化
2. 实现 `FFmpegExecutor` 类
   - 异步命令执行
   - 实时输出捕获
3. 实现 `ProgressParser` 类
   - 解析 FFmpeg 进度输出
   - 提取帧数、时间、速度等信息
4. 错误处理和日志记录
5. 编写单元测试

**依赖**: 阶段 2
**可并行**: CommandBuilder 和 ProgressParser 可并行开发

### 阶段 4: 数据模型（1-2 天）

**任务**:
1. 定义 `ConversionTask` 模型
   - 输入/输出文件
   - 转换参数
   - 任务状态
2. 定义 `FormatConfig` 模型
   - 支持的格式列表
   - 格式特定参数
3. 定义 `FFmpegInfo` 模型
   - FFmpeg 版本信息
   - 支持的编解码器
4. 使用 Pydantic 进行数据验证

**依赖**: 阶段 1
**可并行**: 可与阶段 2、3 并行开发

### 阶段 5: 基础 UI 框架（2-3 天）

**任务**:
1. 创建主应用类 `FFmpegTUIApp`
   - 应用初始化
   - 屏幕管理
   - 全局状态管理
2. 实现 `MainScreen`
   - 主菜单布局
   - 操作选择（转换、压缩、设置）
   - 导航逻辑
3. 创建基础 CSS 样式
   - 颜色主题
   - 布局样式
   - 组件样式
4. 实现应用入口点

**依赖**: 阶段 1
**可并行**: 可与阶段 2、3、4 并行开发

### 阶段 6: 自定义 UI 组件（3-4 天）

**任务**:
1. 实现 `FilePicker` 组件
   - 基于 Textual 的 DirectoryTree
   - 文件过滤（按扩展名）
   - 文件选择事件
2. 实现 `ProgressDisplay` 组件
   - 进度条显示
   - 详细信息（帧数、时间、速度）
   - 取消按钮
3. 实现 `FormatSelector` 组件
   - 格式下拉列表
   - 格式描述显示
4. 实现 `ParameterPanel` 组件
   - 分辨率选择
   - 码率输入
   - 帧率选择
   - 质量预设选择

**依赖**: 阶段 5
**可并行**: 各组件可并行开发

### 阶段 7: 功能屏幕实现（4-5 天）

**任务**:
1. 实现 `ConvertScreen`
   - 文件选择（输入/输出）
   - 格式选择
   - 转换执行
   - 进度显示
2. 实现 `CompressScreen`
   - 文件选择
   - 参数配置（分辨率、码率、帧率）
   - 压缩执行
   - 进度显示
3. 实现 `SettingsScreen`
   - FFmpeg 路径配置
   - 默认参数设置
   - 主题选择
4. 实现屏幕间导航和数据传递

**依赖**: 阶段 6
**可并行**: ConvertScreen 和 CompressScreen 可并行开发

### 阶段 8: 集成和测试（3-4 天）

**任务**:
1. 集成所有模块
   - UI 与核心逻辑连接
   - 事件处理和状态同步
2. 端到端测试
   - 格式转换流程测试
   - 视频压缩流程测试
   - 错误场景测试
3. 跨平台测试
   - Windows 测试
   - macOS 测试
   - Linux 测试
4. 性能优化
   - 异步操作优化
   - UI 响应性优化
5. 修复 Bug

**依赖**: 阶段 7
**可并行**: 不同平台测试可并行进行

### 阶段 9: 文档和发布准备（2-3 天）

**任务**:
1. 编写用户文档
   - 安装指南
   - 使用教程
   - 常见问题
2. 编写开发文档
   - 架构说明
   - API 文档
   - 贡献指南
3. 准备发布
   - 版本号确定
   - 更新日志
   - 打包配置
4. 创建安装包
   - PyPI 发布准备
   - 可执行文件打包（可选）

**依赖**: 阶段 8
**可并行**: 文档编写可部分并行

## 技术栈详细说明

### 核心依赖

```toml
[project]
name = "ffmpeg-tui-tools"
version = "0.1.0"
description = "A TUI tool for simplifying FFmpeg video/audio conversion"
requires-python = ">=3.8"
dependencies = [
    "textual>=0.50.0",      # TUI 框架
    "rich>=13.0.0",         # 终端格式化
    "httpx>=0.25.0",        # HTTP 客户端（下载 FFmpeg）
    "platformdirs>=4.0.0",  # 跨平台目录
    "pydantic>=2.0.0",      # 数据验证
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
```

### 支持的格式

**视频格式**:
- 输入: MP4, AVI, MKV, MOV, FLV, WMV, WEBM
- 输出: MP4, AVI, MKV, MOV, WEBM

**音频格式**:
- 输入: MP3, WAV, AAC, FLAC, OGG, M4A
- 输出: MP3, WAV, AAC, FLAC, OGG

### 压缩参数

**分辨率预设**:
- 4K (3840x2160)
- 1080p (1920x1080)
- 720p (1280x720)
- 480p (854x480)
- 自定义

**码率预设**:
- 高质量: 8000k (视频), 320k (音频)
- 中等质量: 4000k (视频), 192k (音频)
- 低质量: 2000k (视频), 128k (音频)
- 自定义

**帧率选项**:
- 60 fps
- 30 fps
- 24 fps
- 自定义

**质量预设** (x264):
- ultrafast
- superfast
- veryfast
- faster
- fast
- medium (默认)
- slow
- slower
- veryslow

## 并行开发策略

### 可并行开发的模块组

**组 1: 核心逻辑**
- FFmpeg Manager
- Command Builder
- FFmpeg Executor
- Progress Parser

**组 2: 数据层**
- 数据模型定义
- 配置管理
- 工具函数

**组 3: UI 层**
- 基础应用框架
- 自定义组件
- 屏幕实现

**并行开发建议**:
1. 组 2 可以最早开始，与其他组并行
2. 组 1 和组 3 可以同时开发，通过接口定义解耦
3. 使用 Mock 对象进行独立测试

## 风险和挑战

### 技术风险

1. **FFmpeg 下载可靠性**
   - 风险: 下载源可能不稳定或被墙
   - 缓解: 提供多个下载源，支持手动指定路径

2. **跨平台兼容性**
   - 风险: 不同平台的 FFmpeg 行为可能不一致
   - 缓解: 充分的跨平台测试，平台特定处理

3. **进度解析准确性**
   - 风险: FFmpeg 输出格式可能变化
   - 缓解: 使用成熟的解析库，添加容错机制

4. **大文件处理性能**
   - 风险: 处理大文件时可能出现性能问题
   - 缓解: 异步处理，流式读取，进度反馈

### 开发风险

1. **Textual 学习曲线**
   - 风险: 团队对 Textual 不熟悉
   - 缓解: 提前学习文档和示例，从简单组件开始

2. **时间估算偏差**
   - 风险: 实际开发时间可能超出估算
   - 缓解: 预留缓冲时间，优先实现核心功能

## 测试策略

### 单元测试
- 覆盖所有核心模块
- 使用 pytest 和 pytest-asyncio
- Mock FFmpeg 执行以加速测试

### 集成测试
- 测试模块间交互
- 测试完整的转换流程
- 使用小型测试文件

### 端到端测试
- 在真实环境中测试
- 测试所有用户场景
- 跨平台测试

### 性能测试
- 测试大文件处理
- 测试并发转换
- 内存和 CPU 使用监控

## 里程碑

- **M1 (第 2 周)**: 完成项目初始化和 FFmpeg 管理模块
- **M2 (第 4 周)**: 完成核心逻辑和基础 UI 框架
- **M3 (第 6 周)**: 完成所有 UI 组件和功能屏幕
- **M4 (第 8 周)**: 完成集成测试和跨平台测试
- **M5 (第 9 周)**: 完成文档和发布准备

## 参考资源

### Textual 框架
- [Textual 官方文档](https://textual.textualize.io/)
- [Real Python - Textual 教程](https://realpython.com/python-textual/)
- [Building Modern Terminal Apps](https://www.mlhive.com/2026/01/building-modern-terminal-apps-with-python-and-textual)
- [textual-fspicker](https://pypi.org/project/textual-fspicker) - 文件选择器组件

### FFmpeg 资源
- [FFmpeg 官方下载](https://ffmpeg.org/download.html)
- [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases) - 自动化构建
- [gyan.dev](https://www.gyan.dev/) - Windows 构建版本
- [FFmpeg 视频压缩指南](https://32blog.com/en/ffmpeg/ffmpeg-video-compression-guide)
- [FFmpeg 进度解析](https://stackoverflow.com/questions/7632589/getting-realtime-output-from-ffmpeg-to-be-used-in-progress-bar-pyqt4-stdout)

### Python 最佳实践
- [Python 2025 最佳实践](https://nerdleveltech.com/python-best-practices-the-2025-guide-for-clean-fast-and-secure-code)
- [Python 模块化设计](https://labex.io/tutorials/python-how-to-design-modular-python-projects-420186)
- [Clean Architecture 模式](https://dasroot.net/posts/2026/01/modern-python-project-structure-clean-architecture-patterns/)
- [pyproject.toml 完整指南](https://inventivehq.com/blog/pyproject-toml-complete-guide)

### Python 包
- [ffmpeg-downloader](https://pypi.org/project/ffmpeg-downloader/)
- [ffmpeg-progress](https://pypi.org/project/ffmpeg-progress/)
- [better-ffmpeg-progress](https://pypi.org/project/better-ffmpeg-progress/)

## 下一步行动

1. **立即开始**: 创建项目目录结构和 `pyproject.toml`
2. **第一周**: 完成阶段 1 和阶段 2
3. **组建团队**: 如果有多人开发，分配并行任务
4. **设置 CI/CD**: 配置自动化测试和构建流程
5. **创建原型**: 快速创建一个最小可用原型验证技术方案

---

**文档版本**: 1.0
**创建日期**: 2026-03-16
**最后更新**: 2026-03-16
