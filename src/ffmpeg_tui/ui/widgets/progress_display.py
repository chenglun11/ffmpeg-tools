"""Progress display widget for FFmpeg operations."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, ProgressBar, Static


class ProgressDisplay(Widget):
    """Widget displaying conversion progress with details and cancel button."""

    DEFAULT_CSS = """
    ProgressDisplay {
        height: auto;
        width: 100%;
        display: none;
    }
    ProgressDisplay.active {
        display: block;
    }
    ProgressDisplay #progress-section {
        width: 100%;
        height: auto;
        border: round $primary;
        padding: 1 2;
        margin: 1 0;
        background: $surface-darken-1;
    }
    ProgressDisplay #progress-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        width: 100%;
        padding: 0 0 1 0;
    }
    ProgressDisplay ProgressBar {
        width: 100%;
        margin: 0;
    }
    ProgressDisplay #progress-pct {
        text-align: center;
        width: 100%;
        padding: 1 0 0 0;
        text-style: bold;
        color: $accent;
    }
    ProgressDisplay .detail-row {
        layout: horizontal;
        height: auto;
        width: 100%;
        padding: 0;
    }
    ProgressDisplay .detail-label {
        width: 1fr;
        text-align: center;
        color: $text-muted;
    }
    ProgressDisplay #btn-cancel {
        width: auto;
        min-width: 20;
        margin: 1 auto;
    }
    ProgressDisplay #status-msg {
        text-align: center;
        width: 100%;
        padding: 1 0;
    }
    """

    class CancelRequested(Message):
        """Posted when the user requests cancellation."""

    def compose(self) -> ComposeResult:
        with Vertical(id="progress-section"):
            yield Static("正在转换...", id="progress-title")
            yield ProgressBar(total=100, id="progress-bar")
            yield Static("0%", id="progress-pct")
            with Horizontal(classes="detail-row"):
                yield Static("帧: -", id="detail-frame", classes="detail-label")
                yield Static("FPS: -", id="detail-fps", classes="detail-label")
                yield Static("速度: -", id="detail-speed", classes="detail-label")
                yield Static("剩余: -", id="detail-eta", classes="detail-label")
            yield Static("", id="status-msg")
            yield Button("取消转换", id="btn-cancel", variant="error")

    @on(Button.Pressed, "#btn-cancel")
    def _on_cancel(self) -> None:
        self.post_message(self.CancelRequested())

    def show(self) -> None:
        """Show the progress display and reset all values."""
        self.add_class("active")
        self.query_one("#progress-bar", ProgressBar).update(progress=0)
        self.query_one("#progress-pct", Static).update("0%")
        self.query_one("#progress-title", Static).update("正在转换...")
        self.query_one("#detail-frame", Static).update("帧: -")
        self.query_one("#detail-fps", Static).update("FPS: -")
        self.query_one("#detail-speed", Static).update("速度: -")
        self.query_one("#detail-eta", Static).update("剩余: -")
        self.query_one("#status-msg", Static).update("")
        self.query_one("#btn-cancel", Button).disabled = False

    def hide(self) -> None:
        """Hide the progress display."""
        self.remove_class("active")

    def update_progress(
        self,
        percentage: float,
        frame: int = 0,
        fps: float = 0.0,
        speed: float = 0.0,
        eta_seconds: float = 0.0,
    ) -> None:
        """Update all progress fields."""
        pct = min(percentage, 100.0)
        self.query_one("#progress-bar", ProgressBar).update(progress=pct)
        self.query_one("#progress-pct", Static).update(f"{pct:.1f}%")
        self.query_one("#detail-frame", Static).update(f"帧: {frame}")
        self.query_one("#detail-fps", Static).update(f"FPS: {fps:.1f}")
        speed_text = f"{speed:.2f}x" if speed > 0 else "-"
        self.query_one("#detail-speed", Static).update(f"速度: {speed_text}")
        if eta_seconds > 0:
            mins = int(eta_seconds // 60)
            secs = int(eta_seconds % 60)
            self.query_one("#detail-eta", Static).update(f"剩余: {mins:02d}:{secs:02d}")
        else:
            self.query_one("#detail-eta", Static).update("剩余: -")

    def set_completed(self, success: bool, message: str = "") -> None:
        """Mark conversion as completed (success or failure)."""
        self.query_one("#btn-cancel", Button).disabled = True
        if success:
            self.query_one("#progress-bar", ProgressBar).update(progress=100)
            self.query_one("#progress-pct", Static).update("100%")
            self.query_one("#progress-title", Static).update("转换完成!")
            msg = message or "[green]转换成功![/green]"
            self.query_one("#status-msg", Static).update(msg)
        else:
            self.query_one("#progress-title", Static).update("转换失败")
            msg = message or "[red]转换失败，请检查文件和参数。[/red]"
            self.query_one("#status-msg", Static).update(msg)

    def set_cancelled(self) -> None:
        """Mark conversion as cancelled."""
        self.query_one("#btn-cancel", Button).disabled = True
        self.query_one("#progress-title", Static).update("已取消")
        self.query_one("#status-msg", Static).update("[yellow]转换已被用户取消。[/yellow]")
