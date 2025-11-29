"""Unit tests for core types."""

import pytest
from pathlib import Path
from datetime import datetime

from src.core.types import (
    ProcessorCategory,
    SessionStatus,
    FileStatus,
    ParameterSpec,
    ProcessResult,
    FileRecord,
    Session,
    AudioFile,
    SplitConfig,
)


class TestProcessorCategory:
    """Tests for ProcessorCategory enum."""
    
    def test_categories_exist(self):
        """Test all expected categories exist."""
        assert ProcessorCategory.MANIPULATION.value == "manipulation"
        assert ProcessorCategory.ANALYSIS.value == "analysis"
        assert ProcessorCategory.VOICE.value == "voice"
        assert ProcessorCategory.AUTOMATION.value == "automation"


class TestSessionStatus:
    """Tests for SessionStatus enum."""
    
    def test_statuses_exist(self):
        """Test all expected statuses exist."""
        assert SessionStatus.IN_PROGRESS.value == "in_progress"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.FAILED.value == "failed"
        assert SessionStatus.PAUSED.value == "paused"


class TestFileStatus:
    """Tests for FileStatus enum."""
    
    def test_statuses_exist(self):
        """Test all expected file statuses exist."""
        assert FileStatus.PENDING.value == "pending"
        assert FileStatus.PROCESSING.value == "processing"
        assert FileStatus.COMPLETED.value == "completed"
        assert FileStatus.FAILED.value == "failed"
        assert FileStatus.SKIPPED.value == "skipped"


class TestParameterSpec:
    """Tests for ParameterSpec dataclass."""
    
    def test_required_fields(self):
        """Test creating ParameterSpec with required fields."""
        spec = ParameterSpec(
            name="duration",
            type="float",
            description="Duration in milliseconds",
        )
        assert spec.name == "duration"
        assert spec.type == "float"
        assert spec.description == "Duration in milliseconds"
        assert spec.required is False
        assert spec.default is None
    
    def test_all_fields(self):
        """Test creating ParameterSpec with all fields."""
        spec = ParameterSpec(
            name="duration",
            type="float",
            description="Duration in milliseconds",
            required=True,
            default=1000.0,
            choices=None,
            min_value=100.0,
            max_value=60000.0,
        )
        assert spec.required is True
        assert spec.default == 1000.0
        assert spec.min_value == 100.0
        assert spec.max_value == 60000.0


class TestProcessResult:
    """Tests for ProcessResult dataclass."""
    
    def test_success_result(self):
        """Test creating a successful ProcessResult."""
        result = ProcessResult(
            success=True,
            input_path=Path("/input/file.wav"),
            output_paths=[Path("/output/file_001.mp3")],
            metadata={"segment_count": 1},
            processing_time_ms=150.5,
        )
        assert result.success is True
        assert result.input_path == Path("/input/file.wav")
        assert len(result.output_paths) == 1
        assert result.error_message is None
        assert result.metadata["segment_count"] == 1
        assert result.processing_time_ms == 150.5
    
    def test_failed_result(self):
        """Test creating a failed ProcessResult."""
        result = ProcessResult(
            success=False,
            input_path=Path("/input/file.wav"),
            error_message="File not found",
        )
        assert result.success is False
        assert result.error_message == "File not found"
        assert len(result.output_paths) == 0
    
    def test_default_values(self):
        """Test ProcessResult default values."""
        result = ProcessResult(
            success=True,
            input_path=Path("/test.wav"),
        )
        assert result.output_paths == []
        assert result.error_message is None
        assert result.metadata == {}
        assert result.processing_time_ms == 0.0


class TestFileRecord:
    """Tests for FileRecord dataclass."""
    
    def test_default_values(self):
        """Test FileRecord default values."""
        record = FileRecord(file_path=Path("/test.wav"))
        assert record.status == FileStatus.PENDING
        assert record.error_message is None
        assert record.output_paths == []
        assert record.started_at is None
        assert record.processed_at is None
    
    def test_completed_record(self):
        """Test a completed FileRecord."""
        now = datetime.now()
        record = FileRecord(
            file_path=Path("/test.wav"),
            status=FileStatus.COMPLETED,
            output_paths=[Path("/output/test_001.mp3")],
            started_at=now,
            processed_at=now,
        )
        assert record.status == FileStatus.COMPLETED
        assert len(record.output_paths) == 1


class TestSession:
    """Tests for Session dataclass."""
    
    def test_default_values(self):
        """Test Session default values."""
        session = Session(
            session_id="test-123",
            processor_name="splitter-fixed",
        )
        assert session.session_id == "test-123"
        assert session.processor_name == "splitter-fixed"
        assert session.status == SessionStatus.IN_PROGRESS
        assert session.total_files == 0
        assert session.processed_count == 0
        assert session.failed_count == 0
        assert session.files == []
        assert session.config == {}
    
    def test_full_session(self):
        """Test Session with all fields."""
        session = Session(
            session_id="test-456",
            processor_name="converter",
            status=SessionStatus.COMPLETED,
            total_files=10,
            processed_count=9,
            failed_count=1,
            config={"output_format": "mp3"},
        )
        assert session.status == SessionStatus.COMPLETED
        assert session.total_files == 10
        assert session.processed_count == 9
        assert session.failed_count == 1


class TestAudioFile:
    """Tests for AudioFile dataclass."""
    
    def test_audio_file_creation(self):
        """Test creating an AudioFile."""
        audio = AudioFile(
            path=Path("/test/audio.mp3"),
            format="mp3",
            duration_ms=120500.0,
            sample_rate=44100,
            channels=2,
            bitrate=192,
        )
        assert audio.path == Path("/test/audio.mp3")
        assert audio.format == "mp3"
        assert audio.duration_ms == 120500.0
        assert audio.sample_rate == 44100
        assert audio.channels == 2
        assert audio.bitrate == 192
    
    def test_optional_bitrate(self):
        """Test AudioFile with optional bitrate."""
        audio = AudioFile(
            path=Path("/test/audio.wav"),
            format="wav",
            duration_ms=60000.0,
            sample_rate=48000,
            channels=1,
        )
        assert audio.bitrate is None


class TestSplitConfig:
    """Tests for SplitConfig dataclass."""
    
    def test_default_values(self):
        """Test SplitConfig default values."""
        config = SplitConfig()
        assert config.method == "fixed"
        assert config.duration_ms is None
        assert config.output_format is None
        assert config.cleanup_last_segment is True
    
    def test_custom_config(self):
        """Test SplitConfig with custom values."""
        config = SplitConfig(
            method="silence",
            duration_ms=30000.0,
            output_format="wav",
            cleanup_last_segment=False,
        )
        assert config.method == "silence"
        assert config.duration_ms == 30000.0
        assert config.output_format == "wav"
        assert config.cleanup_last_segment is False
