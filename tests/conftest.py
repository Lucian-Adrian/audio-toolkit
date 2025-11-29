"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil

from pydub import AudioSegment
from pydub.generators import Sine


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def output_dir(temp_dir):
    """Create an output directory for tests."""
    output = temp_dir / "output"
    output.mkdir()
    return output


@pytest.fixture
def sample_audio_10sec(temp_dir) -> Path:
    """Create a 10-second mono audio file."""
    # Generate 10 seconds of 440Hz sine wave
    audio = Sine(440).to_audio_segment(duration=10000)
    
    path = temp_dir / "test_10sec.wav"
    audio.export(str(path), format="wav")
    return path


@pytest.fixture
def sample_audio_5sec(temp_dir) -> Path:
    """Create a 5-second mono audio file."""
    audio = Sine(440).to_audio_segment(duration=5000)
    
    path = temp_dir / "test_5sec.wav"
    audio.export(str(path), format="wav")
    return path


@pytest.fixture
def sample_audio_1sec(temp_dir) -> Path:
    """Create a 1-second mono audio file."""
    audio = Sine(440).to_audio_segment(duration=1000)
    
    path = temp_dir / "test_1sec.wav"
    audio.export(str(path), format="wav")
    return path


@pytest.fixture
def sample_audio_dir(temp_dir, sample_audio_10sec, sample_audio_5sec) -> Path:
    """Create a directory with multiple audio files."""
    audio_dir = temp_dir / "audio_files"
    audio_dir.mkdir()
    
    # Copy sample files to the directory
    shutil.copy(sample_audio_10sec, audio_dir / "file1.wav")
    shutil.copy(sample_audio_5sec, audio_dir / "file2.wav")
    
    # Create a subdirectory with more files
    subdir = audio_dir / "subdir"
    subdir.mkdir()
    shutil.copy(sample_audio_5sec, subdir / "file3.wav")
    
    return audio_dir


@pytest.fixture
def empty_file(temp_dir) -> Path:
    """Create an empty file."""
    path = temp_dir / "empty.wav"
    path.touch()
    return path


@pytest.fixture
def invalid_audio_file(temp_dir) -> Path:
    """Create an invalid audio file (text content)."""
    path = temp_dir / "invalid.wav"
    path.write_text("This is not audio data")
    return path
