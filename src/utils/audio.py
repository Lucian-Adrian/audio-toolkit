"""Audio utilities using pydub."""

from pathlib import Path
from typing import Optional, Tuple

from pydub import AudioSegment

from ..core.exceptions import CorruptedFileError, UnsupportedFormatError
from ..core.types import AudioFile
from .file_ops import SUPPORTED_FORMATS
from .logger import get_logger

logger = get_logger(__name__)


def load_audio(path: Path) -> AudioSegment:
    """
    Load an audio file using pydub.
    
    Args:
        path: Path to audio file
        
    Returns:
        AudioSegment object
        
    Raises:
        UnsupportedFormatError: If format is not supported
        CorruptedFileError: If file cannot be loaded
    """
    ext = path.suffix.lower().lstrip(".")
    
    if ext not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(f"Unsupported format: {ext}")
    
    try:
        return AudioSegment.from_file(str(path))
    except Exception as e:
        raise CorruptedFileError(f"Failed to load {path}: {e}")


def get_audio_info(path: Path) -> AudioFile:
    """
    Get audio file information.
    
    Args:
        path: Path to audio file
        
    Returns:
        AudioFile with metadata
        
    Raises:
        CorruptedFileError: If file cannot be read
    """
    try:
        audio = load_audio(path)
        return AudioFile(
            path=path,
            format=path.suffix.lower().lstrip("."),
            duration_ms=len(audio),
            sample_rate=audio.frame_rate,
            channels=audio.channels,
            bitrate=getattr(audio, "bitrate", None),
        )
    except (UnsupportedFormatError, CorruptedFileError):
        raise
    except Exception as e:
        raise CorruptedFileError(f"Failed to get info for {path}: {e}")


def export_audio(
    audio: AudioSegment,
    output_path: Path,
    format: Optional[str] = None,
    bitrate: Optional[str] = None,
) -> Path:
    """
    Export an AudioSegment to a file.
    
    Args:
        audio: AudioSegment to export
        output_path: Output file path
        format: Output format (default: inferred from extension)
        bitrate: Bitrate for lossy formats (e.g., "192k")
        
    Returns:
        Path to exported file
    """
    format = format or output_path.suffix.lower().lstrip(".")
    
    export_params = {}
    if bitrate and format in ("mp3", "aac", "ogg"):
        export_params["bitrate"] = bitrate
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio.export(str(output_path), format=format, **export_params)
    
    logger.debug(f"Exported audio to {output_path}")
    return output_path


def get_duration_ms(path: Path) -> float:
    """Get audio duration in milliseconds."""
    audio = load_audio(path)
    return len(audio)


def split_audio(
    audio: AudioSegment,
    start_ms: float,
    end_ms: float,
) -> AudioSegment:
    """
    Extract a segment from an AudioSegment.
    
    Args:
        audio: Source AudioSegment
        start_ms: Start time in milliseconds
        end_ms: End time in milliseconds
        
    Returns:
        Extracted segment
    """
    return audio[int(start_ms):int(end_ms)]


def calculate_segments(
    duration_ms: float,
    segment_duration_ms: float,
    min_last_segment_ms: float = 1000.0,
) -> list[Tuple[float, float]]:
    """
    Calculate segment boundaries for fixed-duration splitting.
    
    Args:
        duration_ms: Total audio duration in milliseconds
        segment_duration_ms: Target segment duration
        min_last_segment_ms: Minimum length for last segment
        
    Returns:
        List of (start_ms, end_ms) tuples
    """
    segments = []
    start = 0.0
    
    while start < duration_ms:
        end = min(start + segment_duration_ms, duration_ms)
        
        # Handle cleanup of short last segment
        remaining = duration_ms - end
        if 0 < remaining < min_last_segment_ms:
            # Extend this segment to include the remainder
            end = duration_ms
        
        segments.append((start, end))
        start = end
    
    return segments
