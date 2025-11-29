"""Integration tests for CLI commands."""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from src.presentation.cli import app


runner = CliRunner()


class TestVersionCommand:
    """Tests for version command."""
    
    def test_version_shows_output(self):
        """Test version command shows version."""
        result = runner.invoke(app, ["version"])
        
        assert result.exit_code == 0
        assert "Audio Toolkit" in result.output
        assert "0.1.0" in result.output


class TestSplitCommand:
    """Tests for split command."""
    
    def test_split_help(self):
        """Test split command shows help."""
        result = runner.invoke(app, ["split", "--help"])
        
        assert result.exit_code == 0
        assert "split" in result.output.lower()
    
    def test_split_fixed_help(self):
        """Test split fixed subcommand shows help."""
        result = runner.invoke(app, ["split", "fixed", "--help"])
        
        assert result.exit_code == 0
        assert "duration" in result.output.lower()
    
    def test_split_fixed_success(self, sample_audio_10sec, output_dir):
        """Test split fixed command succeeds."""
        result = runner.invoke(app, [
            "split", "fixed",
            str(sample_audio_10sec),
            "--duration", "2",
            "--output", str(output_dir),
            "--quiet",
        ])
        
        assert result.exit_code == 0
        assert "Processed" in result.output or "segments" in result.output.lower()
    
    def test_split_fixed_missing_duration(self, sample_audio_10sec, output_dir):
        """Test split fixed requires duration."""
        result = runner.invoke(app, [
            "split", "fixed",
            str(sample_audio_10sec),
            "--output", str(output_dir),
        ])
        
        assert result.exit_code != 0
    
    def test_split_fixed_nonexistent_file(self, output_dir):
        """Test split fixed with nonexistent file."""
        result = runner.invoke(app, [
            "split", "fixed",
            "nonexistent.wav",
            "--duration", "2",
            "--output", str(output_dir),
        ])
        
        assert result.exit_code != 0


class TestConvertCommand:
    """Tests for convert command."""
    
    def test_convert_help(self):
        """Test convert command shows help."""
        result = runner.invoke(app, ["convert", "--help"])
        
        assert result.exit_code == 0
        assert "convert" in result.output.lower()
    
    def test_convert_files_help(self):
        """Test convert files subcommand shows help."""
        result = runner.invoke(app, ["convert", "files", "--help"])
        
        assert result.exit_code == 0
        assert "format" in result.output.lower()
    
    def test_convert_files_success(self, sample_audio_5sec, output_dir):
        """Test convert files command succeeds."""
        result = runner.invoke(app, [
            "convert", "files",
            str(sample_audio_5sec),
            "--format", "mp3",
            "--output", str(output_dir),
            "--quiet",
        ])
        
        assert result.exit_code == 0
        assert "Converted" in result.output
    
    def test_convert_files_with_normalize(self, sample_audio_5sec, output_dir):
        """Test convert files with normalize option."""
        result = runner.invoke(app, [
            "convert", "files",
            str(sample_audio_5sec),
            "--format", "mp3",
            "--output", str(output_dir),
            "--normalize",
            "--quiet",
        ])
        
        assert result.exit_code == 0


class TestCLINoArgs:
    """Tests for CLI with no arguments."""
    
    def test_no_args_shows_help(self):
        """Test running CLI with no args shows help."""
        result = runner.invoke(app, [])
        
        # Should show help (no_args_is_help=True)
        assert "Usage" in result.output or "Commands" in result.output
