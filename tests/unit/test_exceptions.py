"""Unit tests for core exceptions."""

import pytest

from src.core.exceptions import (
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


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""
    
    def test_base_exception(self):
        """Test AudioToolkitError is base for all exceptions."""
        with pytest.raises(AudioToolkitError):
            raise AudioToolkitError("Test error")
    
    def test_config_errors_inherit_from_base(self):
        """Test config errors inherit from AudioToolkitError."""
        assert issubclass(ConfigError, AudioToolkitError)
        assert issubclass(InvalidYAMLError, ConfigError)
        assert issubclass(MissingParameterError, ConfigError)
    
    def test_processing_errors_inherit_from_base(self):
        """Test processing errors inherit from AudioToolkitError."""
        assert issubclass(ProcessingError, AudioToolkitError)
        assert issubclass(CorruptedFileError, ProcessingError)
        assert issubclass(UnsupportedFormatError, ProcessingError)
        assert issubclass(EmptyFileError, ProcessingError)
    
    def test_validation_errors_inherit_from_base(self):
        """Test validation errors inherit from AudioToolkitError."""
        assert issubclass(ValidationError, AudioToolkitError)
        assert issubclass(InvalidDurationError, ValidationError)
        assert issubclass(InvalidPathError, ValidationError)
    
    def test_session_errors_inherit_from_base(self):
        """Test session errors inherit from AudioToolkitError."""
        assert issubclass(SessionError, AudioToolkitError)
        assert issubclass(SessionLockedError, SessionError)
        assert issubclass(SessionNotFoundError, SessionError)
    
    def test_plugin_errors_inherit_from_base(self):
        """Test plugin errors inherit from AudioToolkitError."""
        assert issubclass(PluginError, AudioToolkitError)
        assert issubclass(PluginNotFoundError, PluginError)
        assert issubclass(PluginInterfaceError, PluginError)


class TestExceptionMessages:
    """Test exception message handling."""
    
    def test_error_message_preserved(self):
        """Test error messages are preserved."""
        msg = "Test error message"
        
        with pytest.raises(AudioToolkitError) as exc:
            raise AudioToolkitError(msg)
        assert str(exc.value) == msg
    
    def test_nested_exception_catching(self):
        """Test catching parent exceptions catches children."""
        with pytest.raises(AudioToolkitError):
            raise InvalidYAMLError("YAML parse error")
        
        with pytest.raises(ConfigError):
            raise MissingParameterError("Missing 'duration'")
        
        with pytest.raises(ProcessingError):
            raise CorruptedFileError("Cannot decode audio")
