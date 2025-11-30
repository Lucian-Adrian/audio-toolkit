"""Tests for Phase 7 CLI commands (analyze and voice)."""

from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import tempfile

import pytest
from typer.testing import CliRunner

from src.presentation.cli import app
from src.core.types import ProcessResult


runner = CliRunner()


class TestAnalyzeCommands:
    """Tests for analyze CLI commands."""
    
    def test_analyze_help(self):
        """Test analyze command shows help."""
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "visualize" in result.output.lower() or "stats" in result.output.lower()
    
    def test_visualize_help(self):
        """Test visualize subcommand shows help."""
        result = runner.invoke(app, ["analyze", "visualize", "--help"])
        assert result.exit_code == 0
        assert "--type" in result.output or "-t" in result.output
        assert "--output" in result.output or "-o" in result.output
    
    def test_stats_help(self):
        """Test stats subcommand shows help."""
        result = runner.invoke(app, ["analyze", "stats", "--help"])
        assert result.exit_code == 0
        assert "--silence-threshold" in result.output or "-s" in result.output
    
    def test_transcribe_help(self):
        """Test transcribe subcommand shows help."""
        result = runner.invoke(app, ["analyze", "transcribe", "--help"])
        assert result.exit_code == 0
        assert "--model" in result.output or "-m" in result.output
        assert "--language" in result.output or "-l" in result.output
    
    @patch("src.presentation.cli.analyze_cmd.get_processor")
    def test_visualize_command_success(self, mock_get_processor, tmp_path):
        """Test visualize command with successful result."""
        # Create test file
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        # Mock processor
        mock_processor = MagicMock()
        mock_processor.process.return_value = ProcessResult(
            success=True,
            input_path=test_file,
            output_paths=[tmp_path / "test_viz.png"],
            processing_time_ms=100.0,
        )
        mock_get_processor.return_value = mock_processor
        
        result = runner.invoke(app, [
            "analyze", "visualize",
            str(test_file),
            "-o", str(tmp_path),
        ])
        
        assert result.exit_code == 0
        mock_get_processor.assert_called_with("visualizer")
        mock_processor.process.assert_called_once()
    
    @patch("src.presentation.cli.analyze_cmd.get_processor")
    def test_stats_command_success(self, mock_get_processor, tmp_path):
        """Test stats command with successful result."""
        # Create test file
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        # Mock processor
        mock_processor = MagicMock()
        mock_processor.process.return_value = ProcessResult(
            success=True,
            input_path=test_file,
            output_paths=[tmp_path / "test_stats.json"],
            metadata={
                "file": {"duration_seconds": 10.0, "sample_rate": 44100, "channels": 2},
                "levels": {"rms_db": -20.0, "peak_db": -3.0, "dynamic_range_db": 15.0},
                "silence": {"percentage": 10.0},
                "vad": {"voice_ratio": 0.8, "voice_segments": 5},
            },
            processing_time_ms=50.0,
        )
        mock_get_processor.return_value = mock_processor
        
        result = runner.invoke(app, [
            "analyze", "stats",
            str(test_file),
        ])
        
        assert result.exit_code == 0
        mock_get_processor.assert_called_with("statistics")
    
    @patch("src.presentation.cli.analyze_cmd.get_processor")
    def test_visualize_command_failure(self, mock_get_processor, tmp_path):
        """Test visualize command handles failure."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        mock_processor = MagicMock()
        mock_processor.process.return_value = ProcessResult(
            success=False,
            input_path=test_file,
            error_message="Missing numpy",
        )
        mock_get_processor.return_value = mock_processor
        
        result = runner.invoke(app, [
            "analyze", "visualize",
            str(test_file),
        ])
        
        assert result.exit_code == 1


class TestVoiceCommands:
    """Tests for voice CLI commands."""
    
    def test_voice_help(self):
        """Test voice command shows help."""
        result = runner.invoke(app, ["voice", "--help"])
        assert result.exit_code == 0
        assert "denoise" in result.output.lower()
        assert "dynamics" in result.output.lower()
        assert "trim" in result.output.lower()
    
    def test_denoise_help(self):
        """Test denoise subcommand shows help."""
        result = runner.invoke(app, ["voice", "denoise", "--help"])
        assert result.exit_code == 0
        assert "--reduction" in result.output or "-r" in result.output
        assert "--noise-floor" in result.output or "-n" in result.output
    
    def test_dynamics_help(self):
        """Test dynamics subcommand shows help."""
        result = runner.invoke(app, ["voice", "dynamics", "--help"])
        assert result.exit_code == 0
        assert "--threshold" in result.output or "-t" in result.output
        assert "--ratio" in result.output or "-r" in result.output
        assert "--eq-low" in result.output or "-l" in result.output
    
    def test_trim_help(self):
        """Test trim subcommand shows help."""
        result = runner.invoke(app, ["voice", "trim", "--help"])
        assert result.exit_code == 0
        assert "--mode" in result.output or "-m" in result.output
        assert "--threshold" in result.output or "-t" in result.output
    
    def test_enhance_help(self):
        """Test enhance subcommand shows help."""
        result = runner.invoke(app, ["voice", "enhance", "--help"])
        assert result.exit_code == 0
        assert "--preset" in result.output or "-p" in result.output
    
    @patch("src.presentation.cli.voice_cmd.get_processor")
    def test_denoise_command_success(self, mock_get_processor, tmp_path):
        """Test denoise command with successful result."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        mock_processor = MagicMock()
        mock_processor.process.return_value = ProcessResult(
            success=True,
            input_path=test_file,
            output_paths=[tmp_path / "test_denoised.wav"],
            processing_time_ms=200.0,
        )
        mock_get_processor.return_value = mock_processor
        
        result = runner.invoke(app, [
            "voice", "denoise",
            str(test_file),
            "-o", str(tmp_path),
        ])
        
        assert result.exit_code == 0
        mock_get_processor.assert_called_with("noise_reduce")
    
    @patch("src.presentation.cli.voice_cmd.get_processor")
    def test_dynamics_command_success(self, mock_get_processor, tmp_path):
        """Test dynamics command with successful result."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        mock_processor = MagicMock()
        mock_processor.process.return_value = ProcessResult(
            success=True,
            input_path=test_file,
            output_paths=[tmp_path / "test_processed.wav"],
            processing_time_ms=150.0,
        )
        mock_get_processor.return_value = mock_processor
        
        result = runner.invoke(app, [
            "voice", "dynamics",
            str(test_file),
            "-t", "-15",
            "-r", "6",
            "-o", str(tmp_path),
        ])
        
        assert result.exit_code == 0
        mock_get_processor.assert_called_with("dynamics")
    
    @patch("src.presentation.cli.voice_cmd.get_processor")
    def test_trim_command_success(self, mock_get_processor, tmp_path):
        """Test trim command with successful result."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        mock_processor = MagicMock()
        mock_processor.process.return_value = ProcessResult(
            success=True,
            input_path=test_file,
            output_paths=[tmp_path / "test_trimmed.wav"],
            metadata={
                "original_duration_ms": 10000,
                "processed_duration_ms": 8000,
                "reduction_percent": 20.0,
            },
            processing_time_ms=100.0,
        )
        mock_get_processor.return_value = mock_processor
        
        result = runner.invoke(app, [
            "voice", "trim",
            str(test_file),
            "-m", "edges",
            "-o", str(tmp_path),
        ])
        
        assert result.exit_code == 0
        mock_get_processor.assert_called_with("trimmer")
    
    @patch("src.presentation.cli.voice_cmd.get_processor")
    def test_enhance_command_success(self, mock_get_processor, tmp_path):
        """Test enhance command with successful result."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        # Mock all three processors called by enhance
        mock_processor = MagicMock()
        intermediate_files = [
            tmp_path / "test_denoised.wav",
            tmp_path / "test_processed.wav",
            tmp_path / "test_trimmed.wav",
        ]
        
        # Create intermediate files
        for f in intermediate_files:
            f.write_bytes(b"fake")
        
        mock_processor.process.side_effect = [
            ProcessResult(success=True, input_path=test_file, output_paths=[intermediate_files[0]], processing_time_ms=100),
            ProcessResult(success=True, input_path=intermediate_files[0], output_paths=[intermediate_files[1]], processing_time_ms=100),
            ProcessResult(success=True, input_path=intermediate_files[1], output_paths=[intermediate_files[2]], processing_time_ms=100),
        ]
        mock_get_processor.return_value = mock_processor
        
        result = runner.invoke(app, [
            "voice", "enhance",
            str(test_file),
            "-p", "podcast",
            "-o", str(tmp_path),
        ])
        
        assert result.exit_code == 0
        # Should call get_processor for noise_reduce, dynamics, trimmer
        assert mock_get_processor.call_count == 3
    
    @patch("src.presentation.cli.voice_cmd.get_processor")
    def test_denoise_command_failure(self, mock_get_processor, tmp_path):
        """Test denoise command handles failure."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")
        
        mock_processor = MagicMock()
        mock_processor.process.return_value = ProcessResult(
            success=False,
            input_path=test_file,
            error_message="Noise floor too short",
        )
        mock_get_processor.return_value = mock_processor
        
        result = runner.invoke(app, [
            "voice", "denoise",
            str(test_file),
        ])
        
        assert result.exit_code == 1


class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    def test_main_help_shows_new_commands(self):
        """Test main help shows analyze and voice commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output.lower()
        assert "voice" in result.output.lower()
    
    def test_all_subcommands_accessible(self):
        """Test all subcommands are accessible."""
        subcommands = [
            ["analyze", "--help"],
            ["analyze", "visualize", "--help"],
            ["analyze", "stats", "--help"],
            ["analyze", "transcribe", "--help"],
            ["voice", "--help"],
            ["voice", "denoise", "--help"],
            ["voice", "dynamics", "--help"],
            ["voice", "trim", "--help"],
            ["voice", "enhance", "--help"],
        ]
        
        for cmd in subcommands:
            result = runner.invoke(app, cmd)
            assert result.exit_code == 0, f"Command {' '.join(cmd)} failed"
