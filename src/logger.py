"""
Logging setup — single call returns a configured logger with file + console output.
"""
import logging
import os


def setup_logger(name: str, log_file: str, level: str = "INFO") -> logging.Logger:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not logger.handlers:          # avoid duplicate handlers on re-import
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
