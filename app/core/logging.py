import logging
import os
from logging.handlers import RotatingFileHandler

from app.core.config import settings


def setup_logging() -> None:
    """Log to console and to a rotating file (logs/app.log)."""
    os.makedirs("logs", exist_ok=True)
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)
    root.handlers = [console, file_handler]