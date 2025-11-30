"""Unit tests for CLI convert command."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from typer.testing import CliRunner

from src.presentation.cli.convert_cmd import app, _format_duration


runner = CliRunner()


class TestConvertFormatDuration:
    """Tests for _format_duration helper in convert module."""
    
    def test_format_seconds_only(self):
        """Test formatting sub-minute durations."""
        assert _format_duration(5000) == "5.0s"
        assert _format_duration(30500) == "30.5s"
    
    def test_format_minutes_and_seconds(self):
        """Test formatting minute-range durations."""
        assert _format_duration(60000) == "1m 0s"
        assert _format_duration(90000) == "1m 30s"
    
    def test_format_hours(self):
        """Test formatting hour-range durations."""
        assert _format_duration(3600000) == "1h 0m"
        assert _format_duration(5400000) == "1h 30m"


class TestConvertFilesCommand:
    """Tests for convert files command."""
    
    @pytest.fixture
    def mock_audio_file(self, tmp_path):
        """Create a mock audio file."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"\x00" * 1024)
        return audio_file
    
    @pytest.fixture
    def mock_audio_dir(self, tmp_path):
        """Create mock directory with audio files."""
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "file1.wav").write_bytes(b"\x00" * 1024)
        (audio_dir / "file2.flac").write_bytes(b"\x00" * 2048)
        return audio_dir
    
    def test_no_files_found_exit_code(self, tmp_path):
        """Test command exits with code 1 when no audio files found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        with patch("src.presentation.cli.convert_cmd.get_audio_files", return_value=[]):
            result = runner.invoke(app, [
                "files",
                str(empty_dir),
            ])
            
            assert result.exit_code == 1
            assert "No audio files found" in result.stdout
    
    def test_dry_run_shows_preview(self, mock_audio_file, tmp_path):
        """Test dry run mode shows preview without processing."""
        with patch("src.presentation.cli.convert_cmd.get_audio_files", return_value=[mock_audio_file]):
            result = runner.invoke(app, [
                "files",
                str(mock_audio_file),
                "-f", "mp3",
                "--dry-run",
            ])
            
            assert result.exit_code == 0
            assert "Dry Run Mode" in result.stdout
            assert "Would convert 1 file" in result.stdout
            assert "test.wav" in result.stdout
    
    def test_dry_run_shows_many_files_truncated(self, tmp_path):
        """Test dry run truncates display at 20 files."""
        # Create 25 mock files
        files = []
        for i in range(25):
            f = tmp_path / f"audio{i}.wav"
            f.write_bytes(b"\x00" * 1024)
            files.append(f)
        
        with patch("src.presentation.cli.convert_cmd.get_audio_files", return_value=files):
            result = runner.invoke(app, [
                "files",
                str(tmp_path),
                "-f", "mp3",
                "--dry-run",
            ])
            
            assert result.exit_code == 0
            assert "and 5 more" in result.stdout
    
    def test_dry_run_shows_processing_options(self, mock_audio_file):
        """Test dry run shows processing options when specified."""
        with patch("src.presentation.cli.convert_cmd.get_audio_files", return_value=[mock_audio_file]):
            result = runner.invoke(app, [
                "files",
                str(mock_audio_file),
                "-f", "mp3",
                "--dry-run",
                "--normalize",
                "--remove-silence",
                "--sample-rate", "44100",
                "--channels", "1",
            ])
            
            assert result.exit_code == 0
            assert "normalize" in result.stdout
            assert "remove silence" in result.stdout
            assert "44100Hz" in result.stdout
            assert "mono" in result.stdout
    
    def test_dry_run_shows_stereo_option(self, mock_audio_file):
        """Test dry run shows stereo when channels=2."""
        with patch("src.presentation.cli.convert_cmd.get_audio_files", return_value=[mock_audio_file]):
            result = runner.invoke(app, [
                "files",
                str(mock_audio_file),
                "-f", "mp3",
                "--dry-run",
                "--channels", "2",
            ])
            
            assert result.exit_code == 0
            assert "stereo" in result.stdout
    
    def test_successful_processing(self, mock_audio_file, tmp_path):
        """Test successful file processing."""
        output_dir = tmp_path / "output"
        
        # Create a mock session result
        from src.core.types import FileStatus
        mock_session = Mock()
        mock_session.processed_count = 1
        mock_session.failed_count = 0
        mock_session.session_id = "test-session-123"
        mock_session.files = [
            Mock(
                status=FileStatus.COMPLETED,
                output_paths=[],
                metadata={"output_duration_ms": 60000}
            )
        ]
        
        mock_manager = Mock()
        mock_manager.run_batch.return_value = mock_session
        
        mock_converter = Mock()
        mock_converter.name = "converter"
        
        with patch("src.presentation.cli.convert_cmd.get_audio_files", return_value=[mock_audio_file]), \
             patch("src.presentation.cli.convert_cmd.get_processor", return_value=mock_converter), \
             patch("src.presentation.cli.convert_cmd.ensure_directory"), \
             patch("src.presentation.cli.convert_cmd.SQLiteSessionStore"), \
             patch("src.presentation.cli.convert_cmd.SessionManager", return_value=mock_manager):
            
            result = runner.invoke(app, [
                "files",
                str(mock_audio_file),
                "-f", "mp3",
                "-o", str(output_dir),
            ])
            
            assert result.exit_code == 0
            assert "Files converted" in result.stdout
            assert "Session ID" in result.stdout
    
    def test_processing_with_all_options(self, mock_audio_file, tmp_path):
        """Test processing passes all options to processor."""
        output_dir = tmp_path / "output"
        
        # Create a mock session result
        from src.core.types import FileStatus
        mock_session = Mock()
        mock_session.processed_count = 1
        mock_session.failed_count = 0
        mock_session.session_id = "test-session-123"
        mock_session.files = [
            Mock(
                status=FileStatus.COMPLETED,
                output_paths=[],
                metadata={"output_duration_ms": 30000}
            )
        ]
        
        mock_manager = Mock()
        mock_manager.run_batch.return_value = mock_session
        
        mock_converter = Mock()
        mock_converter.name = "converter"
        
        with patch("src.presentation.cli.convert_cmd.get_audio_files", return_value=[mock_audio_file]), \
             patch("src.presentation.cli.convert_cmd.get_processor", return_value=mock_converter), \
             patch("src.presentation.cli.convert_cmd.ensure_directory"), \
             patch("src.presentation.cli.convert_cmd.SQLiteSessionStore"), \
             patch("src.presentation.cli.convert_cmd.SessionManager", return_value=mock_manager):
            
            result = runner.invoke(app, [
                "files",
                str(mock_audio_file),
                "-f", "mp3",
                "-o", str(output_dir),
                "-b", "320k",
                "-s", "48000",
                "-c", "2",
                "--normalize",
                "--remove-silence",
            ])
            
            # Verify manager was called - options are now passed via run_batch
            mock_manager.run_batch.assert_called_once()
    
    def test_processing_failure_logged(self, mock_audio_file, tmp_path):
        """Test failed file processing shows error."""
        output_dir = tmp_path / "output"
        
        # Create a mock session result with failure
        from src.core.types import FileStatus
        mock_session = Mock()
        mock_session.processed_count = 0
        mock_session.failed_count = 1
        mock_session.session_id = "test-session-123"
        mock_session.files = [
            Mock(
                status=FileStatus.FAILED,
                output_paths=[],
                error_message="Conversion codec error"
            )
        ]
        
        mock_manager = Mock()
        mock_manager.run_batch.return_value = mock_session
        
        mock_converter = Mock()
        mock_converter.name = "converter"
        
        with patch("src.presentation.cli.convert_cmd.get_audio_files", return_value=[mock_audio_file]), \
             patch("src.presentation.cli.convert_cmd.get_processor", return_value=mock_converter), \
             patch("src.presentation.cli.convert_cmd.ensure_directory"), \
             patch("src.presentation.cli.convert_cmd.SQLiteSessionStore"), \
             patch("src.presentation.cli.convert_cmd.SessionManager", return_value=mock_manager):
            
            result = runner.invoke(app, [
                "files",
                str(mock_audio_file),
                "-f", "mp3",
                "-o", str(output_dir),
            ])
            
            assert "Failed" in result.stdout
    
    def test_quiet_mode_suppresses_errors(self, mock_audio_file, tmp_path):
        """Test quiet mode suppresses individual error messages."""
        output_dir = tmp_path / "output"
        
        # Create a mock session result with failure
        from src.core.types import FileStatus
        mock_session = Mock()
        mock_session.processed_count = 0
        mock_session.failed_count = 1
        mock_session.session_id = "test-session-123"
        mock_session.files = [
            Mock(
                status=FileStatus.FAILED,
                output_paths=[],
                error_message="Some error"
            )
        ]
        
        mock_manager = Mock()
        mock_manager.run_batch.return_value = mock_session
        
        mock_converter = Mock()
        mock_converter.name = "converter"
        
        with patch("src.presentation.cli.convert_cmd.get_audio_files", return_value=[mock_audio_file]), \
             patch("src.presentation.cli.convert_cmd.get_processor", return_value=mock_converter), \
             patch("src.presentation.cli.convert_cmd.ensure_directory"), \
             patch("src.presentation.cli.convert_cmd.SQLiteSessionStore"), \
             patch("src.presentation.cli.convert_cmd.SessionManager", return_value=mock_manager):
            
            result = runner.invoke(app, [
                "files",
                str(mock_audio_file),
                "-f", "mp3",
                "-o", str(output_dir),
                "--quiet",
            ])
            
            # Error message should not appear in quiet mode
            assert "Some error" not in result.stdout
    
    def test_verbose_mode_enables_debug_logging(self, mock_audio_file, tmp_path):
        """Test verbose flag enables debug logging level."""
        output_dir = tmp_path / "output"
        
        # Create a mock session result
        from src.core.types import FileStatus
        mock_session = Mock()
        mock_session.processed_count = 1
        mock_session.failed_count = 0
        mock_session.session_id = "test-session-123"
        mock_session.files = [
            Mock(
                status=FileStatus.COMPLETED,
                output_paths=[],
                metadata={"output_duration_ms": 0}
            )
        ]
        
        mock_manager = Mock()
        mock_manager.run_batch.return_value = mock_session
        
        mock_converter = Mock()
        mock_converter.name = "converter"
        
        with patch("src.presentation.cli.convert_cmd.get_audio_files", return_value=[mock_audio_file]), \
             patch("src.presentation.cli.convert_cmd.get_processor", return_value=mock_converter), \
             patch("src.presentation.cli.convert_cmd.ensure_directory"), \
             patch("src.presentation.cli.convert_cmd.SQLiteSessionStore"), \
             patch("src.presentation.cli.convert_cmd.SessionManager", return_value=mock_manager), \
             patch("src.presentation.cli.convert_cmd.setup_logging") as mock_setup:
            
            result = runner.invoke(app, [
                "files",
                str(mock_audio_file),
                "-f", "mp3",
                "-o", str(output_dir),
                "--verbose",
            ])
            
            # Verify logging was set up with DEBUG level
            import logging
            mock_setup.assert_called_once()
            call_args = mock_setup.call_args
            assert call_args[1]["level"] == logging.DEBUG


class TestConvertCallback:
    """Tests for convert command callback."""
    
    def test_callback_help_text(self):
        """Test callback provides help text."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Convert audio file formats" in result.stdout
