import logging
import logging.handlers
from pathlib import Path
from typing import Optional


LOG_DIR = Path("./logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """Configure root logger with console and rotating file handlers.

    Creates ./logs/trading_news_checker.log by default.
    """
    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    fmt = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
    formatter = logging.Formatter(fmt)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    target = log_file or str(LOG_DIR / "trading_news_checker.log")
    fileh = logging.handlers.RotatingFileHandler(target, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fileh.setFormatter(formatter)
    root.addHandler(fileh)

    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
