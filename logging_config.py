import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


LOG_DIR = Path("./logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _level_from_env(default: int = logging.INFO) -> int:
    val = os.getenv("LOG_LEVEL", "").strip()
    if not val:
        return default
    try:
        return int(val)
    except Exception:
        # allow names like DEBUG, INFO
        return getattr(logging, val.upper(), default)


def setup_logging(level: int | None = None, log_file: Optional[str] = None) -> None:
    """Configure root logger with console and rotating file handlers.

    Respects environment variables:
      - LOG_LEVEL: integer or name (DEBUG, INFO, ...)
      - LOG_FILE: path to a log file (overrides default)

    You can still pass `level` or `log_file` to override env values.
    """
    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    fmt = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
    formatter = logging.Formatter(fmt)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    env_file = os.getenv("LOG_FILE")
    target = log_file or env_file or str(LOG_DIR / "trading_news_checker.log")
    fileh = logging.handlers.RotatingFileHandler(target, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fileh.setFormatter(formatter)
    root.addHandler(fileh)

    lvl = level if level is not None else _level_from_env()
    root.setLevel(lvl)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
