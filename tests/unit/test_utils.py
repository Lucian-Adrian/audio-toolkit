"""Unit tests for utility modules."""

import pytest
from pathlib import Path

from src.utils.file_ops import (
    ensure_directory,
    scan_audio_files,
    get_audio_files,
    is_supported_format,
    generate_output_filename,
    SUPPORTED_FORMATS,
)
from src.utils.validators import (
    validate_input_file,
    validate_duration,
    validate_format,
    collect_validation_errors,
)
from src.utils.audio import calculate_segments
from src.core.exceptions import (
    InvalidPathError,
    EmptyFileError,
    UnsupportedFormatError,
    InvalidDurationError,
)


class TestFileOps:
    """Tests for file operations utilities."""
    
    def test_ensure_directory_creates_dir(self, temp_dir):
        """Test ensure_directory creates a directory."""
        new_dir = temp_dir / "new_subdir"
        assert not new_dir.exists()
        
        result = ensure_directory(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir
    
    def test_ensure_directory_existing(self, temp_dir):
        """Test ensure_directory with existing directory."""
        existing = temp_dir / "existing"
        existing.mkdir()
        
        result = ensure_directory(existing)
        
        assert result == existing
    
    def test_scan_audio_files(self, sample_audio_dir):
        """Test scanning for audio files."""
        files = list(scan_audio_files(sample_audio_dir, recursive=False))
        
        assert len(files) == 2
        assert all(f.suffix == ".wav" for f in files)
    
    def test_scan_audio_files_recursive(self, sample_audio_dir):
        """Test recursive scanning for audio files."""
        files = list(scan_audio_files(sample_audio_dir, recursive=True))
        
        assert len(files) == 3
    
    def test_scan_audio_files_nonexistent(self, temp_dir):
        """Test scanning nonexistent directory raises error."""
        with pytest.raises(InvalidPathError):
            list(scan_audio_files(temp_dir / "nonexistent"))
    
    def test_get_audio_files_sorted(self, sample_audio_dir):
        """Test get_audio_files returns sorted list."""
        files = get_audio_files(sample_audio_dir, recursive=False)
        
        assert isinstance(files, list)
        assert files == sorted(files)
    
    def test_is_supported_format(self):
        """Test is_supported_format."""
        assert is_supported_format(Path("test.mp3"))
        assert is_supported_format(Path("test.WAV"))
        assert is_supported_format(Path("test.flac"))
        assert not is_supported_format(Path("test.txt"))
        assert not is_supported_format(Path("test.pdf"))
    
    def test_supported_formats_constant(self):
        """Test SUPPORTED_FORMATS contains expected formats."""
        assert "mp3" in SUPPORTED_FORMATS
        assert "wav" in SUPPORTED_FORMATS
        assert "flac" in SUPPORTED_FORMATS
        assert "ogg" in SUPPORTED_FORMATS
    
    def test_generate_output_filename(self, temp_dir):
        """Test generate_output_filename."""
        input_path = temp_dir / "original.wav"
        output_dir = temp_dir / "output"
        
        result = generate_output_filename(
            input_path,
            suffix="_segment_001",
            output_dir=output_dir,
            new_extension="mp3",
        )
        
        assert result == output_dir / "original_segment_001.mp3"
    
    def test_generate_output_filename_defaults(self, temp_dir):
        """Test generate_output_filename with defaults."""
        input_path = temp_dir / "test.wav"
        
        result = generate_output_filename(input_path, suffix="_copy")
        
        assert result == temp_dir / "test_copy.wav"


class TestValidators:
    """Tests for validation utilities."""
    
    def test_validate_input_file_success(self, sample_audio_10sec):
        """Test validating a valid audio file."""
        # Should not raise
        validate_input_file(sample_audio_10sec)
    
    def test_validate_input_file_not_found(self, temp_dir):
        """Test validating nonexistent file."""
        with pytest.raises(InvalidPathError, match="not found"):
            validate_input_file(temp_dir / "nonexistent.wav")
    
    def test_validate_input_file_empty(self, empty_file):
        """Test validating empty file."""
        with pytest.raises(EmptyFileError, match="empty"):
            validate_input_file(empty_file)
    
    def test_validate_input_file_unsupported_format(self, temp_dir):
        """Test validating unsupported format."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("not audio")
        
        with pytest.raises(UnsupportedFormatError, match="Unsupported format"):
            validate_input_file(txt_file)
    
    def test_validate_duration_success(self):
        """Test validating valid duration."""
        # Should not raise
        validate_duration(5000.0)
        validate_duration(100.0)
    
    def test_validate_duration_too_short(self):
        """Test validating too short duration."""
        with pytest.raises(InvalidDurationError, match="at least"):
            validate_duration(50.0)
    
    def test_validate_duration_too_long(self):
        """Test validating too long duration."""
        with pytest.raises(InvalidDurationError, match="at most"):
            validate_duration(100000.0, max_ms=60000.0)
    
    def test_validate_format_success(self):
        """Test validating valid formats."""
        validate_format("mp3")
        validate_format("wav")
        validate_format("FLAC")  # Case insensitive
    
    def test_validate_format_unsupported(self):
        """Test validating unsupported format."""
        with pytest.raises(UnsupportedFormatError):
            validate_format("xyz")
    
    def test_collect_validation_errors_none(self, sample_audio_10sec):
        """Test collect_validation_errors with valid inputs."""
        errors = collect_validation_errors(
            path=sample_audio_10sec,
            duration_ms=5000.0,
            format="mp3",
        )
        assert errors == []
    
    def test_collect_validation_errors_multiple(self, temp_dir):
        """Test collect_validation_errors with multiple errors."""
        errors = collect_validation_errors(
            path=temp_dir / "nonexistent.wav",
            duration_ms=10.0,
            format="xyz",
        )
        assert len(errors) == 3


class TestAudioUtils:
    """Tests for audio utilities."""
    
    def test_calculate_segments_exact_division(self):
        """Test segment calculation with exact division."""
        segments = calculate_segments(
            duration_ms=10000.0,
            segment_duration_ms=2000.0,
        )
        
        assert len(segments) == 5
        assert segments[0] == (0.0, 2000.0)
        assert segments[-1] == (8000.0, 10000.0)
    
    def test_calculate_segments_with_remainder(self):
        """Test segment calculation with remainder."""
        segments = calculate_segments(
            duration_ms=10000.0,
            segment_duration_ms=3000.0,
        )
        
        assert len(segments) == 4
        # Last segment should be shorter
        assert segments[-1] == (9000.0, 10000.0)
    
    def test_calculate_segments_cleanup_short_last(self):
        """Test segment calculation merges short last segment."""
        # 10 seconds, 3 second segments
        # Without cleanup: [0-3, 3-6, 6-9, 9-10] = 4 segments
        # With cleanup (min 1 sec): [0-3, 3-6, 6-10] = 3 segments (last extended)
        segments = calculate_segments(
            duration_ms=10000.0,
            segment_duration_ms=3000.0,
            min_last_segment_ms=1500.0,
        )
        
        # Should merge 9-10 with 6-9 since 1000ms < 1500ms
        assert segments[-1][1] == 10000.0
    
    def test_calculate_segments_single_segment(self):
        """Test when audio is shorter than segment duration."""
        segments = calculate_segments(
            duration_ms=5000.0,
            segment_duration_ms=10000.0,
        )
        
        assert len(segments) == 1
        assert segments[0] == (0.0, 5000.0)
