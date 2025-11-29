"""Core module - types, exceptions, and interfaces."""

from .types import (
    ProcessorCategory,
    SessionStatus,
    FileStatus,
    ParameterSpec,
    ProcessResult,
    FileRecord,
    Session,
    AudioFile,
    SplitConfig,
)
from .exceptions import (
    AudioToolkitError,
    ConfigError,
    InvalidYAMLError,
    MissingParameterError,
    ProcessingError,
    CorruptedFileError,
    UnsupportedFormatError,
    EmptyFileError,
    ValidationError,
    InvalidDurationError,
    InvalidPathError,
    SessionError,
    SessionLockedError,
    SessionNotFoundError,
    PluginError,
    PluginNotFoundError,
    PluginInterfaceError,
)
from .interfaces import (
    AudioProcessor,
    SessionStore,
    ProgressReporter,
)

__all__ = [
    # Types
    "ProcessorCategory",
    "SessionStatus",
    "FileStatus",
    "ParameterSpec",
    "ProcessResult",
    "FileRecord",
    "Session",
    "AudioFile",
    "SplitConfig",
    # Exceptions
    "AudioToolkitError",
    "ConfigError",
    "InvalidYAMLError",
    "MissingParameterError",
    "ProcessingError",
    "CorruptedFileError",
    "UnsupportedFormatError",
    "EmptyFileError",
    "ValidationError",
    "InvalidDurationError",
    "InvalidPathError",
    "SessionError",
    "SessionLockedError",
    "SessionNotFoundError",
    "PluginError",
    "PluginNotFoundError",
    "PluginInterfaceError",
    # Interfaces
    "AudioProcessor",
    "SessionStore",
    "ProgressReporter",
]
