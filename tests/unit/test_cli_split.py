"""Unit tests for CLI split command."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from src.presentation.cli.split_cmd import app, _format_duration


runner = CliRunner()


class TestFormatDuration:
    """Tests for _format_duration helper."""
    
    def test_format_seconds_only(self):
        """Test formatting sub-minute durations."""
        assert _format_duration(5000) == "5.0s"
        assert _format_duration(30500) == "30.5s"
        assert _format_duration(0) == "0.0s"
    
    def test_format_minutes_and_seconds(self):
        """Test formatting minute-range durations."""
        assert _format_duration(60000) == "1m 0s"
        assert _format_duration(90000) == "1m 30s"
        assert _format_duration(3599000) == "59m 59s"
    
    def test_format_hours(self):
        """Test formatting hour-range durations."""
        assert _format_duration(3600000) == "1h 0m"
        assert _format_duration(5400000) == "1h 30m"
        assert _format_duration(7200000) == "2h 0m"


class TestSplitFixedCommand:
    """Tests for split fixed command."""
    
    @pytest.fixture
    def mock_audio_file(self, tmp_path):
        """Create a mock audio file."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"\x00" * 1024)
        return audio_file
    
    @pytest.fixture
    def mock_audio_dir(self, tmp_path):
        """Create mock directory with audio files."""
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "file1.mp3").write_bytes(b"\x00" * 1024)
        (audio_dir / "file2.wav").write_bytes(b"\x00" * 2048)
        return audio_dir
    
    def test_no_files_found_exit_code(self, tmp_path):
        """Test command exits with code 1 when no audio files found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        with patch("src.presentation.cli.split_cmd.get_audio_files", return_value=[]):
            result = runner.invoke(app, [
                "fixed",
                str(empty_dir),
                "-d", "10",
            ])
            
            assert result.exit_code == 1
            assert "No audio files found" in result.stdout
    
    def test_dry_run_shows_preview(self, mock_audio_file, tmp_path):
        """Test dry run mode shows preview without processing."""
        with patch("src.presentation.cli.split_cmd.get_audio_files", return_value=[mock_audio_file]):
            result = runner.invoke(app, [
                "fixed",
                str(mock_audio_file),
                "-d", "10",
                "--dry-run",
            ])
            
            assert result.exit_code == 0
            assert "Dry Run Mode" in result.stdout
            assert "Would process 1 file" in result.stdout
            assert "test.mp3" in result.stdout
    
    def test_dry_run_shows_many_files_truncated(self, tmp_path):
        """Test dry run truncates display at 20 files."""
        # Create 25 mock files
        files = []
        for i in range(25):
            f = tmp_path / f"audio{i}.mp3"
            f.write_bytes(b"\x00" * 1024)
            files.append(f)
        
        with patch("src.presentation.cli.split_cmd.get_audio_files", return_value=files):
            result = runner.invoke(app, [
                "fixed",
                str(tmp_path),
                "-d", "10",
                "--dry-run",
            ])
            
            assert result.exit_code == 0
            assert "and 5 more" in result.stdout
    
    def test_successful_processing(self, mock_audio_file, tmp_path):
        """Test successful file processing."""
        output_dir = tmp_path / "output"
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_paths = [Path("seg1.mp3"), Path("seg2.mp3")]
        mock_result.metadata = {"total_duration_ms": 60000}
        
        mock_splitter = Mock()
        mock_splitter.process.return_value = mock_result
        
        with patch("src.presentation.cli.split_cmd.get_audio_files", return_value=[mock_audio_file]), \
             patch("src.presentation.cli.split_cmd.get_processor", return_value=mock_splitter), \
             patch("src.presentation.cli.split_cmd.ensure_directory"):
            
            result = runner.invoke(app, [
                "fixed",
                str(mock_audio_file),
                "-d", "30",
                "-o", str(output_dir),
            ])
            
            assert result.exit_code == 0
            assert "Files processed" in result.stdout
            assert "Segments created" in result.stdout
    
    def test_processing_failure_logged(self, mock_audio_file, tmp_path):
        """Test failed file processing shows error."""
        output_dir = tmp_path / "output"
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "Audio codec error"
        
        mock_splitter = Mock()
        mock_splitter.process.return_value = mock_result
        
        with patch("src.presentation.cli.split_cmd.get_audio_files", return_value=[mock_audio_file]), \
             patch("src.presentation.cli.split_cmd.get_processor", return_value=mock_splitter), \
             patch("src.presentation.cli.split_cmd.ensure_directory"):
            
            result = runner.invoke(app, [
                "fixed",
                str(mock_audio_file),
                "-d", "30",
                "-o", str(output_dir),
            ])
            
            assert "Failed" in result.stdout
            assert "Audio codec error" in result.stdout
    
    def test_quiet_mode_suppresses_errors(self, mock_audio_file, tmp_path):
        """Test quiet mode suppresses individual error messages."""
        output_dir = tmp_path / "output"
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "Some error"
        
        mock_splitter = Mock()
        mock_splitter.process.return_value = mock_result
        
        with patch("src.presentation.cli.split_cmd.get_audio_files", return_value=[mock_audio_file]), \
             patch("src.presentation.cli.split_cmd.get_processor", return_value=mock_splitter), \
             patch("src.presentation.cli.split_cmd.ensure_directory"):
            
            result = runner.invoke(app, [
                "fixed",
                str(mock_audio_file),
                "-d", "30",
                "-o", str(output_dir),
                "--quiet",
            ])
            
            # Error message should not appear in quiet mode
            assert "Some error" not in result.stdout
    
    def test_verbose_mode_enables_debug_logging(self, mock_audio_file, tmp_path):
        """Test verbose flag enables debug logging level."""
        output_dir = tmp_path / "output"
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_paths = []
        mock_result.metadata = {"total_duration_ms": 0}
        
        mock_splitter = Mock()
        mock_splitter.process.return_value = mock_result
        
        with patch("src.presentation.cli.split_cmd.get_audio_files", return_value=[mock_audio_file]), \
             patch("src.presentation.cli.split_cmd.get_processor", return_value=mock_splitter), \
             patch("src.presentation.cli.split_cmd.ensure_directory"), \
             patch("src.presentation.cli.split_cmd.setup_logging") as mock_setup:
            
            result = runner.invoke(app, [
                "fixed",
                str(mock_audio_file),
                "-d", "30",
                "-o", str(output_dir),
                "--verbose",
            ])
            
            # Verify logging was set up with DEBUG level
            import logging
            mock_setup.assert_called_once()
            call_args = mock_setup.call_args
            assert call_args[1]["level"] == logging.DEBUG


class TestSplitCallback:
    """Tests for split command callback."""
    
    def test_callback_help_text(self):
        """Test callback provides help text."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Split audio files into segments" in result.stdout
