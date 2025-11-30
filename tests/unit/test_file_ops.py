"""Unit tests for file operations utilities."""

import pytest
from pathlib import Path

from src.utils.file_ops import (
    ensure_directory,
    scan_audio_files,
    get_audio_files,
    validate_input_path,
    validate_output_directory,
    is_supported_format,
    generate_output_filename,
    SUPPORTED_FORMATS,
)
from src.core.exceptions import InvalidPathError


class TestEnsureDirectory:
    """Tests for ensure_directory function."""
    
    def test_ensure_directory_creates(self, temp_dir):
        """Test directory is created if doesn't exist."""
        new_dir = temp_dir / "new_directory"
        
        result = ensure_directory(new_dir)
        
        assert result == new_dir
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    def test_ensure_directory_exists(self, temp_dir):
        """Test existing directory is returned."""
        result = ensure_directory(temp_dir)
        
        assert result == temp_dir
    
    def test_ensure_directory_nested(self, temp_dir):
        """Test nested directories are created."""
        nested = temp_dir / "level1" / "level2" / "level3"
        
        result = ensure_directory(nested)
        
        assert result == nested
        assert nested.exists()


class TestScanAudioFiles:
    """Tests for scan_audio_files function."""
    
    def test_scan_audio_files_recursive(self, temp_dir):
        """Test scanning recursively finds all audio files."""
        # Create test files
        (temp_dir / "file1.mp3").touch()
        (temp_dir / "file2.wav").touch()
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.flac").touch()
        (temp_dir / "not_audio.txt").touch()
        
        files = list(scan_audio_files(temp_dir, recursive=True))
        
        assert len(files) == 3
        assert all(f.suffix.lstrip(".") in SUPPORTED_FORMATS for f in files)
    
    def test_scan_audio_files_non_recursive(self, temp_dir):
        """Test scanning non-recursively."""
        (temp_dir / "file1.mp3").touch()
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file2.mp3").touch()
        
        files = list(scan_audio_files(temp_dir, recursive=False))
        
        assert len(files) == 1
    
    def test_scan_audio_files_filter_formats(self, temp_dir):
        """Test filtering by format."""
        (temp_dir / "file1.mp3").touch()
        (temp_dir / "file2.wav").touch()
        (temp_dir / "file3.flac").touch()
        
        files = list(scan_audio_files(temp_dir, formats={"mp3", "wav"}))
        
        assert len(files) == 2
    
    def test_scan_audio_files_not_found(self, temp_dir):
        """Test scanning nonexistent directory raises error."""
        nonexistent = temp_dir / "nonexistent"
        
        with pytest.raises(InvalidPathError) as exc_info:
            list(scan_audio_files(nonexistent))
        
        assert "not found" in str(exc_info.value)
    
    def test_scan_audio_files_not_directory(self, temp_dir):
        """Test scanning non-directory raises error."""
        file_path = temp_dir / "file.txt"
        file_path.touch()
        
        with pytest.raises(InvalidPathError) as exc_info:
            list(scan_audio_files(file_path))
        
        assert "not a directory" in str(exc_info.value)


class TestGetAudioFiles:
    """Tests for get_audio_files function."""
    
    def test_get_audio_files_sorted(self, temp_dir):
        """Test files are returned sorted."""
        (temp_dir / "c.mp3").touch()
        (temp_dir / "a.mp3").touch()
        (temp_dir / "b.mp3").touch()
        
        files = get_audio_files(temp_dir)
        
        assert [f.name for f in files] == ["a.mp3", "b.mp3", "c.mp3"]


class TestValidateInputPath:
    """Tests for validate_input_path function."""
    
    def test_validate_input_path_exists(self, temp_dir):
        """Test validating existing file."""
        file_path = temp_dir / "test.txt"
        file_path.touch()
        
        result = validate_input_path(file_path)
        
        assert result == file_path
    
    def test_validate_input_path_not_exists(self, temp_dir):
        """Test validating nonexistent file raises error."""
        nonexistent = temp_dir / "nonexistent.txt"
        
        with pytest.raises(InvalidPathError) as exc_info:
            validate_input_path(nonexistent)
        
        assert "not found" in str(exc_info.value)
    
    def test_validate_input_path_must_exist_false(self, temp_dir):
        """Test validating with must_exist=False."""
        nonexistent = temp_dir / "nonexistent.txt"
        
        result = validate_input_path(nonexistent, must_exist=False)
        
        assert result == nonexistent
    
    def test_validate_input_path_is_directory(self, temp_dir):
        """Test validating directory raises error."""
        with pytest.raises(InvalidPathError) as exc_info:
            validate_input_path(temp_dir)
        
        assert "not a file" in str(exc_info.value)


class TestValidateOutputDirectory:
    """Tests for validate_output_directory function."""
    
    def test_validate_output_directory_creates(self, temp_dir):
        """Test directory is created if doesn't exist."""
        new_dir = temp_dir / "output"
        
        result = validate_output_directory(new_dir)
        
        assert result == new_dir
        assert new_dir.exists()


class TestIsSupportedFormat:
    """Tests for is_supported_format function."""
    
    def test_supported_mp3(self, temp_dir):
        """Test MP3 is supported."""
        path = temp_dir / "test.mp3"
        
        assert is_supported_format(path) is True
    
    def test_supported_wav(self, temp_dir):
        """Test WAV is supported."""
        path = temp_dir / "test.wav"
        
        assert is_supported_format(path) is True
    
    def test_unsupported(self, temp_dir):
        """Test unsupported format."""
        path = temp_dir / "test.txt"
        
        assert is_supported_format(path) is False
    
    def test_uppercase_extension(self, temp_dir):
        """Test uppercase extension is supported."""
        path = temp_dir / "test.MP3"
        
        assert is_supported_format(path) is True


class TestGenerateOutputFilename:
    """Tests for generate_output_filename function."""
    
    def test_generate_output_filename_default(self, temp_dir):
        """Test generating filename with defaults."""
        input_path = temp_dir / "input.wav"
        
        result = generate_output_filename(input_path, "_segment_001")
        
        assert result.name == "input_segment_001.wav"
        assert result.parent == temp_dir
    
    def test_generate_output_filename_custom_dir(self, temp_dir):
        """Test generating filename with custom output dir."""
        input_path = temp_dir / "input.wav"
        output_dir = temp_dir / "output"
        
        result = generate_output_filename(input_path, "_segment_001", output_dir=output_dir)
        
        assert result.parent == output_dir
    
    def test_generate_output_filename_new_extension(self, temp_dir):
        """Test generating filename with new extension."""
        input_path = temp_dir / "input.wav"
        
        result = generate_output_filename(input_path, "_converted", new_extension="mp3")
        
        assert result.name == "input_converted.mp3"
