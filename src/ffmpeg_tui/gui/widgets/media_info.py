"""Media info display widget — shows ffprobe analysis results."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QGroupBox, QLabel

from ffmpeg_tui.utils.file_utils import format_duration, format_file_size


def _format_bitrate(bps: int) -> str:
    if bps <= 0:
        return ""
    kbps = bps / 1000
    if kbps >= 1000:
        return f"{kbps / 1000:.1f} Mbps"
    return f"{kbps:.0f} kbps"


class MediaInfoWidget(QGroupBox):
    """Displays detailed media probe information in a compact grid."""

    def __init__(self, parent=None) -> None:
        super().__init__("文件分析", parent)
        self._grid = QGridLayout(self)
        self._grid.setSpacing(2)
        self._grid.setContentsMargins(10, 6, 10, 6)
        self._grid.setColumnMinimumWidth(0, 70)
        self._widgets: list[QLabel] = []
        self.hide()

    def _add_row(self, row: int, key: str, value: str) -> int:
        k = QLabel(key)
        k.setStyleSheet("color: #6b7280; font-size: 12px; padding: 0; margin: 0;")
        v = QLabel(value)
        v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.setStyleSheet("color: #1f2937; font-size: 13px; padding: 0; margin: 0;")
        self._grid.addWidget(k, row, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self._grid.addWidget(v, row, 1)
        self._widgets.extend([k, v])
        return row + 1

    def _add_header(self, row: int, text: str) -> int:
        h = QLabel(text)
        h.setStyleSheet(
            "font-weight: bold; color: #7c3aed; font-size: 12px; "
            "padding: 2px 0 0 0; margin: 0;"
        )
        self._grid.addWidget(h, row, 0, 1, 2)
        self._widgets.append(h)
        return row + 1

    def clear(self) -> None:
        for w in self._widgets:
            self._grid.removeWidget(w)
            w.deleteLater()
        self._widgets.clear()
        self.hide()

    def update_info(self, probe: dict, file_size: int = 0) -> None:
        self.clear()
        row = 0

        # General summary line
        parts: list[str] = []
        if probe.get("format_name"):
            parts.append(probe["format_name"])
        if file_size > 0:
            parts.append(format_file_size(file_size))
        elif probe.get("size"):
            parts.append(format_file_size(probe["size"]))
        if probe.get("duration", 0) > 0:
            parts.append(format_duration(probe["duration"]))
        br = _format_bitrate(probe.get("bit_rate", 0))
        if br:
            parts.append(br)
        if parts:
            summary = QLabel("  |  ".join(parts))
            summary.setWordWrap(True)
            summary.setStyleSheet("color: #1f2937; font-size: 13px; padding: 0; margin: 0;")
            self._grid.addWidget(summary, row, 0, 1, 2)
            self._widgets.append(summary)
            row += 1

        # Video stream
        video = probe.get("video")
        if video:
            row = self._add_header(row, "视频流")
            codec = video.get("codec", "")
            short = video.get("codec_short", "")
            codec_text = f"{codec} ({short})" if short and short != codec else codec
            if codec_text:
                row = self._add_row(row, "编码:", codec_text)
            w, h = video.get("width", 0), video.get("height", 0)
            if w and h:
                row = self._add_row(row, "分辨率:", f"{w} x {h}")
            fps = video.get("fps", 0)
            if fps > 0:
                row = self._add_row(row, "帧率:", f"{fps:g} fps")
            pix = video.get("pix_fmt", "")
            if pix:
                row = self._add_row(row, "像素格式:", pix)
            vbr = _format_bitrate(video.get("bit_rate", 0))
            if vbr:
                row = self._add_row(row, "码率:", vbr)

        # Audio stream
        audio = probe.get("audio")
        if audio:
            row = self._add_header(row, "音频流")
            codec = audio.get("codec", "")
            short = audio.get("codec_short", "")
            codec_text = f"{codec} ({short})" if short and short != codec else codec
            if codec_text:
                row = self._add_row(row, "编码:", codec_text)
            sr = audio.get("sample_rate", 0)
            if sr > 0:
                row = self._add_row(row, "采样率:", f"{sr} Hz")
            ch = audio.get("channels", 0)
            ch_layout = audio.get("channel_layout", "")
            if ch > 0:
                ch_text = f"{ch} 声道"
                if ch_layout:
                    ch_text += f" ({ch_layout})"
                row = self._add_row(row, "声道:", ch_text)
            abr = _format_bitrate(audio.get("bit_rate", 0))
            if abr:
                row = self._add_row(row, "码率:", abr)

        self.show()
