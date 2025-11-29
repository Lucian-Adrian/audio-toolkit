"""Custom exception hierarchy for the audio toolkit."""


class AudioToolkitError(Exception):
    """Base exception for all Audio Toolkit errors."""
    pass


# Configuration Errors
class ConfigError(AudioToolkitError):
    """Invalid configuration."""
    pass


class InvalidYAMLError(ConfigError):
    """YAML parsing failed."""
    pass


class MissingParameterError(ConfigError):
    """Required parameter not provided."""
    pass


# Processing Errors
class ProcessingError(AudioToolkitError):
    """Error during audio processing."""
    pass


class CorruptedFileError(ProcessingError):
    """Audio file is corrupted or unreadable."""
    pass


class UnsupportedFormatError(ProcessingError):
    """Audio format not supported."""
    pass


class EmptyFileError(ProcessingError):
    """Audio file is empty (zero bytes)."""
    pass


# Validation Errors
class ValidationError(AudioToolkitError):
    """Input validation failed."""
    pass


class InvalidDurationError(ValidationError):
    """Invalid duration specified."""
    pass


class InvalidPathError(ValidationError):
    """Invalid file or directory path."""
    pass


# Session Errors
class SessionError(AudioToolkitError):
    """Session management error."""
    pass


class SessionLockedError(SessionError):
    """Session is locked by another process."""
    pass


class SessionNotFoundError(SessionError):
    """Session ID not found."""
    pass


# Plugin Errors
class PluginError(AudioToolkitError):
    """Plugin system error."""
    pass


class PluginNotFoundError(PluginError):
    """Plugin not found in registry."""
    pass


class PluginInterfaceError(PluginError):
    """Plugin does not implement required interface."""
    pass
