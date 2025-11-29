"""Integration tests for audio processing."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
import pydub

from src.core.types import AudioFile, ProcessingConfig, SplitConfig
from src.processors.converter import AudioConverter
from src.processors.splitter.fixed import FixedDurationSplitter
from src.utils.audio import load_audio_file
from src.utils.validators import AudioFileValidator


@pytest.fixture
def sample_audio():
    """Create a sample audio file for testing."""
    # Create a simple audio segment
    audio = pydub.AudioSegment.silent(duration=5000, frame_rate=44100)  # 5 seconds

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        audio.export(f.name, format='wav')
        yield Path(f.name)

    # Cleanup
    Path(f.name).unlink(missing_ok=True)


class TestAudioConverter:
    """Integration tests for AudioConverter."""

    def test_convert_wav_to_mp3(self, sample_audio):
        """Test converting WAV to MP3."""
        converter = AudioConverter()
        audio_file = load_audio_file(sample_audio)

        config = ProcessingConfig(
            output_format='mp3',
            quality=128
        )

        result = converter.process(audio_file, config)

        assert result.success
        assert result.output_file.path.exists()
        assert result.output_file.format == 'mp3'
        assert result.output_file.path.suffix == '.mp3'

        # Cleanup
        result.output_file.path.unlink(missing_ok=True)

    def test_convert_with_normalization(self, sample_audio):
        """Test converting with normalization."""
        converter = AudioConverter()
        audio_file = load_audio_file(sample_audio)

        config = ProcessingConfig(
            output_format='mp3',
            normalize=True
        )

        result = converter.process(audio_file, config)

        assert result.success
        assert result.output_file.path.exists()

        # Cleanup
        result.output_file.path.unlink(missing_ok=True)


class TestFixedDurationSplitter:
    """Integration tests for FixedDurationSplitter."""

    def test_split_into_segments(self, sample_audio):
        """Test splitting audio into fixed duration segments."""
        splitter = FixedDurationSplitter()
        audio_file = load_audio_file(sample_audio)

        config = SplitConfig(
            duration=2.0,  # 2 seconds per segment
            output_prefix='test_segment'
        )

        result = splitter.split(audio_file, config)

        assert result.success
        assert len(result.output_files) == 3  # 5 seconds / 2 seconds = 2.5, so 3 segments

        # Check that output files exist and have correct duration
        for output_file in result.output_files:
            assert output_file.path.exists()
            loaded = load_audio_file(output_file.path)
            assert abs(loaded.duration - 2.0) < 0.1 or output_file == result.output_files[-1]  # Last can be shorter

        # Cleanup
        for output_file in result.output_files:
            output_file.path.unlink(missing_ok=True)


class TestAudioValidator:
    """Integration tests for AudioValidator."""

    def test_validate_valid_file(self, sample_audio):
        """Test validating a valid audio file."""
        validator = AudioFileValidator()
        audio_file = load_audio_file(sample_audio)

        assert validator.validate(audio_file)
        assert len(validator.get_validation_errors(audio_file)) == 0

    def test_validate_invalid_format(self, tmp_path):
        """Test validating a file with invalid format."""
        # Create a text file
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("not audio")

        audio_file = AudioFile(
            path=invalid_file,
            format='txt',
            duration=0,
            sample_rate=0,
            channels=0
        )

        validator = AudioFileValidator()
        assert not validator.validate(audio_file)
        errors = validator.get_validation_errors(audio_file)
        assert len(errors) > 0
        assert any("format" in error.lower() for error in errors)