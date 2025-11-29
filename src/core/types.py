"""Core type definitions for the audio toolkit."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProcessorCategory(Enum):
    """Categories for organizing processors in UI."""
    MANIPULATION = "manipulation"
    ANALYSIS = "analysis"
    VOICE = "voice"
    AUTOMATION = "automation"


class SessionStatus(Enum):
    """Status of a processing session."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class FileStatus(Enum):
    """Status of a file in a session."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ParameterSpec:
    """Specification for a processor parameter (used for CLI/TUI generation)."""
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None
    choices: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class ProcessResult:
    """Result of a single file processing operation."""
    success: bool
    input_path: Path
    output_paths: List[Path] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0


@dataclass
class FileRecord:
    """Tracks processing state of a single file."""
    file_path: Path
    status: FileStatus = FileStatus.PENDING
    error_message: Optional[str] = None
    output_paths: List[Path] = field(default_factory=list)
    started_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


@dataclass
class Session:
    """Represents a batch processing session."""
    session_id: str
    processor_name: str
    status: SessionStatus = SessionStatus.IN_PROGRESS
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    config: Dict[str, Any] = field(default_factory=dict)
    total_files: int = 0
    processed_count: int = 0
    failed_count: int = 0
    files: List[FileRecord] = field(default_factory=list)


@dataclass
class AudioFile:
    """Represents an audio file with metadata."""
    path: Path
    format: str
    duration_ms: float
    sample_rate: int
    channels: int
    bitrate: Optional[int] = None


@dataclass
class SplitConfig:
    """Configuration for audio splitting operations."""
    method: str = "fixed"
    duration_ms: Optional[float] = None
    output_format: Optional[str] = None
    cleanup_last_segment: bool = True
