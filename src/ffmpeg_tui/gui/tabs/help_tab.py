"""Help tab: usage guide and keyboard shortcuts."""

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ffmpeg_tui import __version__


class HelpTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        clayout = QVBoxLayout(content)
        clayout.setContentsMargins(24, 20, 24, 20)
        clayout.setSpacing(16)

        # --- Header ---
        header = QLabel("FFmpeg Tools 使用指南")
        hfont = QFont()
        hfont.setPointSize(18)
        hfont.setBold(True)
        header.setFont(hfont)
        header.setStyleSheet("color: #7c3aed;")
        clayout.addWidget(header)

        subtitle = QLabel(f"版本 {__version__}")
        subtitle.setStyleSheet("color: #9ca3af; font-size: 12px;")
        clayout.addWidget(subtitle)

        # --- Quick start ---
        clayout.addWidget(self._section("快速开始"))
        clayout.addWidget(self._text(
            "1. 确保 FFmpeg 已安装（可在「设置」页一键下载安装）\n"
            "2. 选择需要的功能页面（格式转换 / 视频压缩 / Meta 专版）\n"
            "3. 选择输入文件，配置参数，点击开始转换"
        ))

        # --- Tab descriptions ---
        clayout.addWidget(self._section("功能说明"))

        clayout.addWidget(self._subsection("格式转换"))
        clayout.addWidget(self._text(
            "将视频/音频文件转换为不同格式。支持选择容器格式（MP4、MKV、"
            "WebM 等）和编解码器（H.264、H.265、VP9 等）。可自定义输出路径。"
        ))

        clayout.addWidget(self._subsection("视频压缩"))
        clayout.addWidget(self._text(
            "在保持可接受画质的前提下压缩视频文件体积。支持调节 CRF 值"
            "（数值越大压缩越强、画质越低），可选择不同的编码预设。"
        ))

        clayout.addWidget(self._subsection("Meta 专版"))
        clayout.addWidget(self._text(
            "针对 Meta 平台（Facebook / Instagram）优化的快捷转换方案，"
            "自动应用推荐参数以满足平台上传要求。"
        ))

        clayout.addWidget(self._subsection("设置"))
        clayout.addWidget(self._text(
            "查看 FFmpeg 安装状态、一键下载安装 FFmpeg、检查软件更新。"
        ))

        # --- FAQ ---
        clayout.addWidget(self._section("常见问题"))

        clayout.addWidget(self._subsection("提示「FFmpeg 未安装」怎么办？"))
        clayout.addWidget(self._text(
            "前往「设置」页面，点击「下载安装 FFmpeg」按钮，程序会自动"
            "下载并配置适合您系统的 FFmpeg。"
        ))

        clayout.addWidget(self._subsection("转换按钮是灰色的无法点击？"))
        clayout.addWidget(self._text(
            "这说明 FFmpeg 尚未安装或未被检测到。请前往「设置」页面安装或"
            "点击「重新检测」。"
        ))

        clayout.addWidget(self._subsection("转换过程中可以取消吗？"))
        clayout.addWidget(self._text(
            "可以。转换开始后会出现取消按钮，点击即可中止当前任务。"
        ))

        clayout.addWidget(self._subsection("支持哪些格式？"))
        clayout.addWidget(self._text(
            "支持 FFmpeg 所支持的所有格式，包括但不限于：\n"
            "视频：MP4、MKV、WebM、AVI、MOV、FLV\n"
            "音频：MP3、AAC、FLAC、WAV、OGG"
        ))

        # --- Links ---
        clayout.addWidget(self._section("相关链接"))

        links_row = QHBoxLayout()
        gh_btn = QPushButton("GitHub 仓库")
        gh_btn.setObjectName("primaryBtn")
        gh_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/chenglun11/ffmpeg-tools")
            )
        )
        links_row.addWidget(gh_btn)

        issue_btn = QPushButton("报告问题")
        issue_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/chenglun11/ffmpeg-tools/issues")
            )
        )
        links_row.addWidget(issue_btn)
        links_row.addStretch()
        clayout.addLayout(links_row)

        clayout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    @staticmethod
    def _section(title: str) -> QLabel:
        label = QLabel(title)
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        label.setFont(font)
        label.setStyleSheet(
            "color: #1f2937; margin-top: 8px; padding-top: 8px; "
            "border-top: 1px solid #e5e7eb;"
        )
        return label

    @staticmethod
    def _subsection(title: str) -> QLabel:
        label = QLabel(title)
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        label.setFont(font)
        label.setStyleSheet("color: #4b5563; margin-top: 2px;")
        return label

    @staticmethod
    def _text(content: str) -> QLabel:
        label = QLabel(content)
        label.setWordWrap(True)
        label.setStyleSheet(
            "color: #374151; font-size: 13px; line-height: 1.6; "
            "padding-left: 8px;"
        )
        return label
