"""File operations utilities."""

from pathlib import Path
from typing import Generator, List, Optional, Set

from ..core.exceptions import InvalidPathError
from .logger import get_logger

logger = get_logger(__name__)

# Supported audio formats
SUPPORTED_FORMATS: Set[str] = {"mp3", "wav", "flac", "ogg", "aac", "m4a"}


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        The path that was ensured
        
    Raises:
        InvalidPathError: If directory cannot be created
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError as e:
        raise InvalidPathError(f"Cannot create directory {path}: {e}")


def scan_audio_files(
    directory: Path,
    formats: Optional[Set[str]] = None,
    recursive: bool = True,
) -> Generator[Path, None, None]:
    """
    Scan a directory for audio files.
    
    Args:
        directory: Directory to scan
        formats: Set of formats to include (default: all supported)
        recursive: Whether to scan subdirectories
        
    Yields:
        Paths to audio files
        
    Raises:
        InvalidPathError: If directory doesn't exist
    """
    if not directory.exists():
        raise InvalidPathError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise InvalidPathError(f"Path is not a directory: {directory}")
    
    formats = formats or SUPPORTED_FORMATS
    
    pattern = "**/*" if recursive else "*"
    
    for path in directory.glob(pattern):
        if path.is_file() and path.suffix.lower().lstrip(".") in formats:
            yield path


def get_audio_files(
    directory: Path,
    formats: Optional[Set[str]] = None,
    recursive: bool = True,
) -> List[Path]:
    """
    Get a list of audio files in a directory.
    
    Args:
        directory: Directory to scan
        formats: Set of formats to include (default: all supported)
        recursive: Whether to scan subdirectories
        
    Returns:
        Sorted list of audio file paths
    """
    return sorted(scan_audio_files(directory, formats, recursive))


def validate_input_path(path: Path, must_exist: bool = True) -> Path:
    """
    Validate an input file path.
    
    Args:
        path: Path to validate
        must_exist: Whether the path must exist
        
    Returns:
        Validated path
        
    Raises:
        InvalidPathError: If validation fails
    """
    if must_exist and not path.exists():
        raise InvalidPathError(f"File not found: {path}")
    
    if path.exists() and not path.is_file():
        raise InvalidPathError(f"Path is not a file: {path}")
    
    return path


def validate_output_directory(path: Path) -> Path:
    """
    Validate and ensure an output directory exists.
    
    Args:
        path: Directory path
        
    Returns:
        Validated and created directory path
        
    Raises:
        InvalidPathError: If directory cannot be created
    """
    return ensure_directory(path)


def is_supported_format(path: Path) -> bool:
    """Check if a file has a supported audio format."""
    return path.suffix.lower().lstrip(".") in SUPPORTED_FORMATS


def generate_output_filename(
    input_path: Path,
    suffix: str,
    output_dir: Optional[Path] = None,
    new_extension: Optional[str] = None,
) -> Path:
    """
    Generate an output filename based on input file.
    
    Args:
        input_path: Original input file path
        suffix: Suffix to add (e.g., "_segment_001")
        output_dir: Output directory (default: same as input)
        new_extension: New file extension (default: same as input)
        
    Returns:
        Generated output path
    """
    output_dir = output_dir or input_path.parent
    extension = new_extension or input_path.suffix.lstrip(".")
    
    return output_dir / f"{input_path.stem}{suffix}.{extension}"
