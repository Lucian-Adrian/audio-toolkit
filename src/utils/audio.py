"""Audio processing utilities using pydub."""

from pathlib import Path
from typing import Optional
import pydub
from ..core.types import AudioFile
from ..core.exceptions import InvalidAudioFormatError, AudioProcessingError
from .logger import logger


def load_audio_file(file_path: Path) -> AudioFile:
    """Load an audio file and return AudioFile metadata."""
    try:
        audio = pydub.AudioSegment.from_file(str(file_path))
        return AudioFile(
            path=file_path,
            format=file_path.suffix[1:].lower(),
            duration=len(audio) / 1000.0,  # pydub uses milliseconds
            sample_rate=audio.frame_rate,
            channels=audio.channels,
            bitrate=getattr(audio, 'bitrate', None)
        )
    except Exception as e:
        logger.error(f"Failed to load audio file {file_path}: {e}")
        raise AudioProcessingError(f"Failed to load audio file: {e}")


def validate_audio_format(file_path: Path, supported_formats: set = {'mp3', 'wav', 'flac', 'aac'}) -> bool:
    """Validate if the audio file format is supported."""
    format = file_path.suffix[1:].lower()
    if format not in supported_formats:
        raise InvalidAudioFormatError(f"Unsupported format: {format}")
    return True


def get_audio_duration(file_path: Path) -> float:
    """Get the duration of an audio file in seconds."""
    try:
        audio = pydub.AudioSegment.from_file(str(file_path))
        return len(audio) / 1000.0
    except Exception as e:
        logger.error(f"Failed to get duration for {file_path}: {e}")
        raise AudioProcessingError(f"Failed to get duration: {e}")


def extract_audio_segment(
    file_path: Path,
    start_time: float,
    end_time: float,
    output_path: Optional[Path] = None
) -> Path:
    """Extract a segment from an audio file."""
    try:
        audio = pydub.AudioSegment.from_file(str(file_path))
        segment = audio[start_time * 1000:end_time * 1000]

        if output_path is None:
            output_path = file_path.parent / f"{file_path.stem}_segment{file_path.suffix}"

        segment.export(str(output_path), format=output_path.suffix[1:])
        logger.debug(f"Extracted segment from {file_path} to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to extract segment from {file_path}: {e}")
        raise AudioProcessingError(f"Failed to extract segment: {e}")