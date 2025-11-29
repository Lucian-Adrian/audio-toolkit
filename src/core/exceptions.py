"""Custom exceptions for the audio toolkit."""


class AudioToolkitError(Exception):
    """Base exception for audio toolkit errors."""
    pass


class InvalidAudioFormatError(AudioToolkitError):
    """Raised when an invalid audio format is encountered."""
    pass


class AudioProcessingError(AudioToolkitError):
    """Raised when audio processing fails."""
    pass


class FileNotFoundError(AudioToolkitError):
    """Raised when an audio file is not found."""
    pass


class ConfigurationError(AudioToolkitError):
    """Raised when configuration is invalid."""
    pass


class ValidationError(AudioToolkitError):
    """Raised when input validation fails."""
    pass