"""File operations utilities for the audio toolkit."""

import shutil
from pathlib import Path
from typing import List, Set
from .logger import logger


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {path}")
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise


def get_audio_files(directory: Path, extensions: Set[str] = {'.mp3', '.wav', '.flac', '.aac'}) -> List[Path]:
    """Get all audio files in a directory with specified extensions."""
    audio_files = []
    for ext in extensions:
        audio_files.extend(directory.rglob(f"*{ext}"))
    return sorted(audio_files)


def copy_file(src: Path, dst: Path, overwrite: bool = False) -> None:
    """Copy a file from src to dst."""
    if dst.exists() and not overwrite:
        logger.warning(f"File {dst} already exists, skipping copy")
        return

    try:
        shutil.copy2(src, dst)
        logger.debug(f"Copied {src} to {dst}")
    except Exception as e:
        logger.error(f"Failed to copy {src} to {dst}: {e}")
        raise


def move_file(src: Path, dst: Path, overwrite: bool = False) -> None:
    """Move a file from src to dst."""
    if dst.exists() and not overwrite:
        logger.warning(f"File {dst} already exists, skipping move")
        return

    try:
        shutil.move(str(src), str(dst))
        logger.debug(f"Moved {src} to {dst}")
    except Exception as e:
        logger.error(f"Failed to move {src} to {dst}: {e}")
        raise


def delete_file(path: Path) -> None:
    """Delete a file if it exists."""
    if path.exists():
        try:
            path.unlink()
            logger.debug(f"Deleted {path}")
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
            raise
    else:
        logger.warning(f"File {path} does not exist, cannot delete")


def get_file_size(path: Path) -> int:
    """Get the size of a file in bytes."""
    try:
        return path.stat().st_size
    except Exception as e:
        logger.error(f"Failed to get size of {path}: {e}")
        raise
