"""Unit tests for custom exceptions."""

import pytest
from src.core.exceptions import (
    AudioToolkitError,
    InvalidAudioFormatError,
    AudioProcessingError,
    FileNotFoundError,
    ConfigurationError,
    ValidationError
)


class TestExceptions:
    """Test custom exceptions."""

    def test_base_exception(self):
        """Test base AudioToolkitError."""
        with pytest.raises(AudioToolkitError):
            raise AudioToolkitError("Test error")

    def test_invalid_format_error(self):
        """Test InvalidAudioFormatError."""
        with pytest.raises(InvalidAudioFormatError):
            raise InvalidAudioFormatError("Invalid format")

        with pytest.raises(AudioToolkitError):
            raise InvalidAudioFormatError("Invalid format")

    def test_audio_processing_error(self):
        """Test AudioProcessingError."""
        with pytest.raises(AudioProcessingError):
            raise AudioProcessingError("Processing failed")

        with pytest.raises(AudioToolkitError):
            raise AudioProcessingError("Processing failed")

    def test_file_not_found_error(self):
        """Test FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            raise FileNotFoundError("File not found")

        with pytest.raises(AudioToolkitError):
            raise FileNotFoundError("File not found")

    def test_configuration_error(self):
        """Test ConfigurationError."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Config error")

        with pytest.raises(AudioToolkitError):
            raise ConfigurationError("Config error")

    def test_validation_error(self):
        """Test ValidationError."""
        with pytest.raises(ValidationError):
            raise ValidationError("Validation failed")

        with pytest.raises(AudioToolkitError):
            raise ValidationError("Validation failed")