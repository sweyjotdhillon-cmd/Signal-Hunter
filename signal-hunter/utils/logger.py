"""
Signal Hunter Logger Utility.

Provides standard logger configuration with support for console formatting and file output.
"""

import logging
import os
import sys
from typing import Optional


def setup_logger(
    name: str = "signal_hunter",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and retrieve a custom logger with standardized formatting.

    Args:
        name (str): Name of the logger, typically __name__ of calling module.
        log_level (str): String logging level (DEBUG, INFO, WARNING, ERROR).
        log_file (Optional[str]): Optional file path to stream logs.

    Returns:
        logging.Logger: Preconfigured logging instance.
    """
    logger = logging.getLogger(name)

    # If the logger is already configured, return it to prevent duplicate handlers
    if logger.handlers:
        return logger

    # Resolve level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Formatter configuration
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console stdout handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        # Create directories if they do not exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
