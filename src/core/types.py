"""Type definitions for the audio toolkit."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class AudioFile:
    """Represents an audio file with metadata."""
    path: Path
    format: str
    duration: float
    sample_rate: int
    channels: int
    bitrate: Optional[int] = None


@dataclass
class ProcessingConfig:
    """Configuration for audio processing operations."""
    output_format: str = "mp3"
    quality: int = 128
    normalize: bool = False
    remove_silence: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SplitConfig:
    """Configuration for audio splitting operations."""
    method: str = "fixed"
    duration: Optional[float] = None
    segments: Optional[List[float]] = None
    output_prefix: str = "segment"


@dataclass
class ConversionResult:
    """Result of an audio conversion operation."""
    input_file: AudioFile
    output_file: AudioFile
    success: bool
    error_message: Optional[str] = None
    processing_time: float = 0.0


@dataclass
class SplitResult:
    """Result of an audio splitting operation."""
    input_file: AudioFile
    output_files: List[AudioFile]
    success: bool
    error_message: Optional[str] = None
    processing_time: float = 0.0