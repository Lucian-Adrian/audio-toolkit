"""Additional unit tests for validators module."""

import pytest
from pathlib import Path

from src.utils.validators import (
    validate_input_file,
    validate_output_directory,
    validate_duration,
    validate_positive_number,
    validate_format,
    collect_validation_errors,
)
from src.core.exceptions import (
    InvalidPathError,
    EmptyFileError,
    UnsupportedFormatError,
    InvalidDurationError,
    ValidationError,
)


class TestValidateInputFileEdgeCases:
    """Additional edge case tests for validate_input_file."""
    
    def test_validate_path_is_directory_not_file(self, tmp_path):
        """Test that directory path raises InvalidPathError."""
        with pytest.raises(InvalidPathError) as exc_info:
            validate_input_file(tmp_path)
        
        assert "not a file" in str(exc_info.value)
    
    def test_validate_empty_file(self, tmp_path):
        """Test that empty file raises EmptyFileError."""
        empty_file = tmp_path / "empty.mp3"
        empty_file.touch()  # Creates empty file
        
        with pytest.raises(EmptyFileError) as exc_info:
            validate_input_file(empty_file)
        
        assert "empty" in str(exc_info.value).lower()


class TestValidateDurationEdgeCases:
    """Additional tests for validate_duration."""
    
    def test_validate_duration_with_max(self):
        """Test validation with max_ms constraint."""
        # Should pass - within range
        validate_duration(5000, min_ms=1000, max_ms=10000)
        
        # Should fail - exceeds max
        with pytest.raises(InvalidDurationError) as exc_info:
            validate_duration(15000, min_ms=1000, max_ms=10000)
        
        assert "at most" in str(exc_info.value)
    
    def test_validate_duration_at_exact_min(self):
        """Test duration exactly at minimum."""
        validate_duration(100, min_ms=100)  # Should pass
    
    def test_validate_duration_at_exact_max(self):
        """Test duration exactly at maximum."""
        validate_duration(10000, min_ms=100, max_ms=10000)  # Should pass


class TestValidatePositiveNumber:
    """Tests for validate_positive_number."""
    
    def test_positive_number_valid(self):
        """Test valid positive numbers."""
        validate_positive_number(1.0, "test")
        validate_positive_number(0.001, "test")
        validate_positive_number(1000000, "test")
    
    def test_zero_not_allowed_by_default(self):
        """Test that zero raises ValidationError by default."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_number(0, "duration")
        
        assert "must be positive" in str(exc_info.value)
    
    def test_zero_allowed_when_specified(self):
        """Test that zero is accepted when allow_zero=True."""
        validate_positive_number(0, "offset", allow_zero=True)
    
    def test_negative_always_fails(self):
        """Test that negative values always fail."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_number(-1, "value")
        
        assert "must be positive" in str(exc_info.value)
    
    def test_negative_fails_even_with_allow_zero(self):
        """Test negative fails even when zero is allowed."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_number(-1, "value", allow_zero=True)
        
        assert "non-negative" in str(exc_info.value)


class TestCollectValidationErrors:
    """Tests for collect_validation_errors function."""
    
    def test_collect_all_valid(self, tmp_path):
        """Test collection with all valid inputs."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"\x00" * 100)
        
        errors = collect_validation_errors(
            path=audio_file,
            duration_ms=5000,
            format="mp3",
        )
        
        assert errors == []
    
    def test_collect_path_error(self):
        """Test collection catches path validation errors."""
        errors = collect_validation_errors(
            path=Path("/nonexistent/file.mp3"),
        )
        
        assert len(errors) == 1
        assert "not found" in errors[0].lower()
    
    def test_collect_duration_error(self):
        """Test collection catches duration validation errors."""
        errors = collect_validation_errors(
            duration_ms=10,  # Below minimum of 100ms
        )
        
        assert len(errors) == 1
        assert "100" in errors[0]  # Message contains 100 (could be 100ms or 100.0ms)
    
    def test_collect_format_error(self):
        """Test collection catches format validation errors."""
        errors = collect_validation_errors(
            format="xyz",  # Invalid format
        )
        
        assert len(errors) == 1
        assert "unsupported" in errors[0].lower()
    
    def test_collect_multiple_errors(self):
        """Test collection of multiple errors."""
        errors = collect_validation_errors(
            path=Path("/nonexistent.txt"),
            duration_ms=10,
            format="invalid",
        )
        
        assert len(errors) == 3
    
    def test_collect_no_params(self):
        """Test collection with no parameters."""
        errors = collect_validation_errors()
        
        assert errors == []
