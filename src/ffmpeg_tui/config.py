"""Configuration management for FFmpeg TUI."""

from pathlib import Path

from platformdirs import user_config_dir, user_data_dir, user_log_dir

APP_NAME = "ffmpeg-tui"

CONFIG_DIR = Path(user_config_dir(APP_NAME))
DATA_DIR = Path(user_data_dir(APP_NAME))
LOG_DIR = Path(user_log_dir(APP_NAME))
FFMPEG_DIR = DATA_DIR / "ffmpeg"
