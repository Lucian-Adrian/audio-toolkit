"""Input validation utilities."""

from pathlib import Path
from typing import List
from ..core.types import AudioFile
from ..core.interfaces import AudioValidator
from ..core.exceptions import ValidationError
from .audio import validate_audio_format
from .logger import logger


class AudioFileValidator(AudioValidator):
    """Validator for audio files."""

    def __init__(self, supported_formats: set = {'mp3', 'wav', 'flac', 'aac'}):
        self.supported_formats = supported_formats

    def validate(self, audio_file: AudioFile) -> bool:
        """Validate an audio file."""
        errors = self.get_validation_errors(audio_file)
        return len(errors) == 0

    def get_validation_errors(self, audio_file: AudioFile) -> List[str]:
        """Get validation errors for an audio file."""
        errors = []

        # Check if file exists
        if not audio_file.path.exists():
            errors.append(f"File does not exist: {audio_file.path}")
            return errors

        # Check if it's a file
        if not audio_file.path.is_file():
            errors.append(f"Path is not a file: {audio_file.path}")
            return errors

        # Check format
        try:
            validate_audio_format(audio_file.path, self.supported_formats)
        except Exception as e:
            errors.append(str(e))

        # Check file size (not empty)
        if audio_file.path.stat().st_size == 0:
            errors.append("File is empty")

        # Check duration (positive)
        if audio_file.duration <= 0:
            errors.append("Invalid duration")

        # Check sample rate
        if audio_file.sample_rate <= 0:
            errors.append("Invalid sample rate")

        # Check channels
        if audio_file.channels <= 0:
            errors.append("Invalid number of channels")

        return errors


def validate_output_directory(output_dir: Path) -> None:
    """Validate output directory."""
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValidationError(f"Cannot create output directory: {e}")

    if not output_dir.is_dir():
        raise ValidationError(f"Output path is not a directory: {output_dir}")


def validate_positive_number(value: float, name: str) -> None:
    """Validate that a number is positive."""
    if value <= 0:
        raise ValidationError(f"{name} must be positive, got {value}")


def validate_file_list(file_paths: List[Path]) -> List[Path]:
    """Validate a list of file paths and return valid ones."""
    valid_files = []
    for path in file_paths:
        if path.exists() and path.is_file():
            valid_files.append(path)
        else:
            logger.warning(f"Invalid file path: {path}")
    return valid_files