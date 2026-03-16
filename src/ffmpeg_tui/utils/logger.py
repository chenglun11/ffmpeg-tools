import logging
from pathlib import Path
from .platform_utils import get_log_dir

def setup_logger(name: str = "ffmpeg_tui", level: int = logging.INFO) -> logging.Logger:
    """配置并返回 logger"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 文件 handler
    log_dir = get_log_dir()
    log_file = log_dir / "ffmpeg_tui.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(file_handler)

    return logger
