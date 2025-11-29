"""Input validation utilities."""

from pathlib import Path
from typing import List, Optional, Set

from ..core.exceptions import (
    EmptyFileError,
    InvalidDurationError,
    InvalidPathError,
    UnsupportedFormatError,
    ValidationError,
)
from .file_ops import SUPPORTED_FORMATS


def validate_input_file(
    path: Path,
    formats: Optional[Set[str]] = None,
) -> None:
    """
    Validate an input audio file.
    
    Args:
        path: Path to validate
        formats: Allowed formats (default: all supported)
        
    Raises:
        InvalidPathError: If path doesn't exist or isn't a file
        EmptyFileError: If file is empty
        UnsupportedFormatError: If format isn't supported
    """
    if not path.exists():
        raise InvalidPathError(f"File not found: {path}")
    
    if not path.is_file():
        raise InvalidPathError(f"Path is not a file: {path}")
    
    if path.stat().st_size == 0:
        raise EmptyFileError(f"File is empty: {path}")
    
    formats = formats or SUPPORTED_FORMATS
    ext = path.suffix.lower().lstrip(".")
    if ext not in formats:
        raise UnsupportedFormatError(
            f"Unsupported format: {ext}. Supported: {', '.join(sorted(formats))}"
        )


def validate_output_directory(path: Path) -> None:
    """
    Validate an output directory.
    
    Args:
        path: Directory path
        
    Raises:
        InvalidPathError: If path exists but isn't a directory
    """
    if path.exists() and not path.is_dir():
        raise InvalidPathError(f"Output path is not a directory: {path}")


def validate_duration(
    duration_ms: float,
    min_ms: float = 100.0,
    max_ms: Optional[float] = None,
) -> None:
    """
    Validate a duration value.
    
    Args:
        duration_ms: Duration in milliseconds
        min_ms: Minimum allowed duration
        max_ms: Maximum allowed duration (optional)
        
    Raises:
        InvalidDurationError: If duration is invalid
    """
    if duration_ms < min_ms:
        raise InvalidDurationError(
            f"Duration must be at least {min_ms}ms, got {duration_ms}ms"
        )
    
    if max_ms is not None and duration_ms > max_ms:
        raise InvalidDurationError(
            f"Duration must be at most {max_ms}ms, got {duration_ms}ms"
        )


def validate_positive_number(
    value: float,
    name: str,
    allow_zero: bool = False,
) -> None:
    """
    Validate that a number is positive.
    
    Args:
        value: Value to validate
        name: Parameter name for error message
        allow_zero: Whether zero is allowed
        
    Raises:
        ValidationError: If validation fails
    """
    if allow_zero:
        if value < 0:
            raise ValidationError(f"{name} must be non-negative, got {value}")
    else:
        if value <= 0:
            raise ValidationError(f"{name} must be positive, got {value}")


def validate_format(
    format: str,
    formats: Optional[Set[str]] = None,
) -> None:
    """
    Validate an audio format.
    
    Args:
        format: Format to validate
        formats: Allowed formats (default: all supported)
        
    Raises:
        UnsupportedFormatError: If format isn't supported
    """
    formats = formats or SUPPORTED_FORMATS
    if format.lower() not in formats:
        raise UnsupportedFormatError(
            f"Unsupported format: {format}. Supported: {', '.join(sorted(formats))}"
        )


def collect_validation_errors(
    path: Optional[Path] = None,
    duration_ms: Optional[float] = None,
    format: Optional[str] = None,
) -> List[str]:
    """
    Collect validation errors without raising exceptions.
    
    Args:
        path: Optional path to validate
        duration_ms: Optional duration to validate
        format: Optional format to validate
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors = []
    
    if path is not None:
        try:
            validate_input_file(path)
        except (InvalidPathError, EmptyFileError, UnsupportedFormatError) as e:
            errors.append(str(e))
    
    if duration_ms is not None:
        try:
            validate_duration(duration_ms)
        except InvalidDurationError as e:
            errors.append(str(e))
    
    if format is not None:
        try:
            validate_format(format)
        except UnsupportedFormatError as e:
            errors.append(str(e))
    
    return errors
