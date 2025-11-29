"""Unit tests for core types."""

import pytest
from pathlib import Path
from src.core.types import AudioFile, ProcessingConfig, SplitConfig, ConversionResult, SplitResult


class TestAudioFile:
    """Test AudioFile dataclass."""

    def test_audio_file_creation(self):
        """Test creating an AudioFile instance."""
        path = Path("/test/audio.mp3")
        audio = AudioFile(
            path=path,
            format="mp3",
            duration=120.5,
            sample_rate=44100,
            channels=2,
            bitrate=128
        )

        assert audio.path == path
        assert audio.format == "mp3"
        assert audio.duration == 120.5
        assert audio.sample_rate == 44100
        assert audio.channels == 2
        assert audio.bitrate == 128


class TestProcessingConfig:
    """Test ProcessingConfig dataclass."""

    def test_default_config(self):
        """Test default processing config."""
        config = ProcessingConfig()
        assert config.output_format == "mp3"
        assert config.quality == 128
        assert config.normalize is False
        assert config.remove_silence is False
        assert config.metadata is None

    def test_custom_config(self):
        """Test custom processing config."""
        config = ProcessingConfig(
            output_format="wav",
            quality=256,
            normalize=True,
            remove_silence=True,
            metadata={"artist": "Test"}
        )
        assert config.output_format == "wav"
        assert config.quality == 256
        assert config.normalize is True
        assert config.remove_silence is True
        assert config.metadata == {"artist": "Test"}


class TestSplitConfig:
    """Test SplitConfig dataclass."""

    def test_default_split_config(self):
        """Test default split config."""
        config = SplitConfig()
        assert config.method == "fixed"
        assert config.duration is None
        assert config.segments is None
        assert config.output_prefix == "segment"


class TestConversionResult:
    """Test ConversionResult dataclass."""

    def test_success_result(self):
        """Test successful conversion result."""
        input_file = AudioFile(Path("/input.mp3"), "mp3", 100, 44100, 2)
        output_file = AudioFile(Path("/output.wav"), "wav", 100, 44100, 2)

        result = ConversionResult(
            input_file=input_file,
            output_file=output_file,
            success=True,
            processing_time=1.5
        )

        assert result.input_file == input_file
        assert result.output_file == output_file
        assert result.success is True
        assert result.error_message is None
        assert result.processing_time == 1.5

    def test_failure_result(self):
        """Test failed conversion result."""
        input_file = AudioFile(Path("/input.mp3"), "mp3", 100, 44100, 2)

        result = ConversionResult(
            input_file=input_file,
            output_file=input_file,  # dummy
            success=False,
            error_message="Conversion failed",
            processing_time=0.0
        )

        assert result.success is False
        assert result.error_message == "Conversion failed"


class TestSplitResult:
    """Test SplitResult dataclass."""

    def test_success_split_result(self):
        """Test successful split result."""
        input_file = AudioFile(Path("/input.mp3"), "mp3", 100, 44100, 2)
        output_files = [
            AudioFile(Path("/output_001.mp3"), "mp3", 30, 44100, 2),
            AudioFile(Path("/output_002.mp3"), "mp3", 30, 44100, 2),
            AudioFile(Path("/output_003.mp3"), "mp3", 40, 44100, 2)
        ]

        result = SplitResult(
            input_file=input_file,
            output_files=output_files,
            success=True,
            processing_time=2.0
        )

        assert result.input_file == input_file
        assert len(result.output_files) == 3
        assert result.success is True
        assert result.error_message is None
        assert result.processing_time == 2.0