"""Logging utilities with Rich formatting."""

import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

# Global console for Rich output
console = Console()

# Default log format
LOG_FORMAT = "%(message)s"
LOG_DATE_FORMAT = "[%X]"


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    rich_tracebacks: bool = True,
) -> logging.Logger:
    """
    Set up logging with Rich console handler and optional file handler.
    
    Args:
        level: Logging level (default INFO)
        log_file: Optional path to log file
        rich_tracebacks: Whether to use Rich for tracebacks
        
    Returns:
        Configured logger instance
    """
    # Get or create the audio toolkit logger
    logger = logging.getLogger("audio_toolkit")
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Add Rich console handler
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=rich_tracebacks,
        tracebacks_show_locals=True,
    )
    rich_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    rich_handler.setLevel(level)
    logger.addHandler(rich_handler)
    
    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "audio_toolkit") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


# Initialize default logger
logger = setup_logging()
