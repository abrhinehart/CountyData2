import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(verbose=False):
    """Configure logging for the commission module.

    Logs to both console (stderr) and a rotating file.
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    logger = logging.getLogger("commission_radar")
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stderr so it doesn't interfere with CLI output)
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(log_level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler (rotating, 5MB max, 3 backups)
    log_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(log_dir, "commission_radar.log")
    file_handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
