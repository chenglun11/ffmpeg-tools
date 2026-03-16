"""Entry point for ffmpeg-tui."""

from ffmpeg_tui.app import FFmpegTUIApp


def main():
    app = FFmpegTUIApp()
    app.run()


if __name__ == "__main__":
    main()
