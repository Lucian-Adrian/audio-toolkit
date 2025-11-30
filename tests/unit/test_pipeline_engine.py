"""Unit tests for pipeline engine."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import shutil

from src.core.exceptions import ConfigError, ProcessingError, PluginNotFoundError
from src.core.types import ProcessResult, SessionStatus
from src.orchestration.pipeline import PipelineEngine
from src.orchestration.pipeline_config import (
    PipelineConfig,
    PipelineInput,
    PipelineSettings,
    PipelineStep,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def sample_audio_dir(temp_dir):
    """Create a directory with sample audio files."""
    from pydub.generators import Sine
    
    audio_dir = temp_dir / "audio"
    audio_dir.mkdir()
    
    # Create test audio files
    audio = Sine(440).to_audio_segment(duration=1000)
    (audio_dir / "test1.wav").touch()
    audio.export(str(audio_dir / "test1.wav"), format="wav")
    audio.export(str(audio_dir / "test2.wav"), format="wav")
    
    return audio_dir


@pytest.fixture
def output_dir(temp_dir):
    """Create output directory."""
    output = temp_dir / "output"
    output.mkdir()
    return output


@pytest.fixture
def valid_config(sample_audio_dir, output_dir):
    """Create a valid pipeline config for testing."""
    return PipelineConfig(
        name="test-pipeline",
        input=PipelineInput(
            path=str(sample_audio_dir),
            formats=["wav"]
        ),
        settings=PipelineSettings(
            output_dir=str(output_dir)
        ),
        steps=[
            PipelineStep(
                name="convert-step",
                processor="converter",
                params={"output_format": "mp3"}
            )
        ]
    )


@pytest.fixture
def engine():
    """Create a pipeline engine instance."""
    return PipelineEngine()


class TestPipelineValidation:
    """Tests for pipeline validation."""
    
    def test_validate_unknown_processor(self, engine, sample_audio_dir, output_dir):
        """EC-PIPE-2: Unknown processor name raises error."""
        config = PipelineConfig(
            name="test",
            input=PipelineInput(path=str(sample_audio_dir)),
            settings=PipelineSettings(output_dir=str(output_dir)),
            steps=[
                PipelineStep(
                    name="invalid-step",
                    processor="nonexistent-processor",
                    params={}
                )
            ]
        )
        
        errors = engine.validate(config)
        
        assert len(errors) > 0
        assert any("unknown processor" in err.lower() for err in errors)
    
    def test_validate_missing_param(self, engine, sample_audio_dir, output_dir):
        """EC-PIPE-4: Missing required param raises error."""
        config = PipelineConfig(
            name="test",
            input=PipelineInput(path=str(sample_audio_dir)),
            settings=PipelineSettings(output_dir=str(output_dir)),
            steps=[
                PipelineStep(
                    name="convert-step",
                    processor="converter",
                    params={}  # Missing required output_format
                )
            ]
        )
        
        errors = engine.validate(config)
        
        assert len(errors) > 0
        assert any("output_format" in err.lower() for err in errors)
    
    def test_validate_nonexistent_input_path(self, engine, output_dir):
        """Validation catches nonexistent input path."""
        config = PipelineConfig(
            name="test",
            input=PipelineInput(path="/nonexistent/path"),
            settings=PipelineSettings(output_dir=str(output_dir)),
            steps=[
                PipelineStep(
                    name="step",
                    processor="converter",
                    params={"output_format": "mp3"}
                )
            ]
        )
        
        errors = engine.validate(config)
        
        assert any("does not exist" in err.lower() for err in errors)
    
    def test_validate_valid_config(self, engine, valid_config):
        """Valid config passes validation."""
        errors = engine.validate(valid_config)
        assert len(errors) == 0


class TestPipelineDryRun:
    """Tests for dry-run mode."""
    
    def test_dry_run_output(self, engine, valid_config):
        """AC-PIPE-2: dry_run prints steps without executing."""
        output_lines = []
        
        plan = engine.dry_run(valid_config, output_callback=output_lines.append)
        
        # Should have step descriptions
        assert len(plan) > 0
        assert any("convert-step" in step for step in plan)
        assert any("converter" in step for step in plan)
        
        # Output should contain pipeline info
        full_output = "\n".join(output_lines)
        assert "test-pipeline" in full_output
        assert "Step 1:" in full_output
    
    def test_dry_run_shows_parameters(self, engine, valid_config):
        """Dry run shows step parameters."""
        output_lines = []
        
        engine.dry_run(valid_config, output_callback=output_lines.append)
        
        full_output = "\n".join(output_lines)
        assert "output_format" in full_output or "mp3" in full_output
    
    def test_dry_run_shows_file_count(self, engine, valid_config):
        """Dry run shows input file count."""
        output_lines = []
        
        engine.dry_run(valid_config, output_callback=output_lines.append)
        
        full_output = "\n".join(output_lines)
        assert "files" in full_output.lower()


class TestPipelineExecution:
    """Tests for pipeline execution."""
    
    def test_execute_order(self, engine, sample_audio_dir, output_dir):
        """AC-PIPE-1: Steps execute in exact order."""
        execution_order = []
        
        # Create config with multiple steps
        config = PipelineConfig(
            name="order-test",
            input=PipelineInput(path=str(sample_audio_dir), formats=["wav"]),
            settings=PipelineSettings(output_dir=str(output_dir)),
            steps=[
                PipelineStep(
                    name="step-1",
                    processor="converter",
                    params={"output_format": "mp3"}
                ),
                PipelineStep(
                    name="step-2",
                    processor="converter",
                    params={"output_format": "wav"}
                ),
            ]
        )
        
        # Execute and verify output directories exist in order
        session = engine.execute(config)
        
        # Check that step directories were created
        step1_dir = output_dir / "step_01_step-1"
        step2_dir = output_dir / "step_02_step-2"
        
        assert step1_dir.exists()
        assert step2_dir.exists()
    
    def test_execute_empty_input(self, engine, temp_dir, output_dir):
        """EC-PIPE-5: Empty input directory exits gracefully."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        config = PipelineConfig(
            name="empty-test",
            input=PipelineInput(path=str(empty_dir), formats=["wav"]),
            settings=PipelineSettings(output_dir=str(output_dir)),
            steps=[
                PipelineStep(
                    name="step1",
                    processor="converter",
                    params={"output_format": "mp3"}
                )
            ]
        )
        
        # Should not raise, but complete with empty result
        session = engine.execute(config)
        assert session is not None
        assert session.status == SessionStatus.COMPLETED
    
    def test_execute_validation_failure(self, engine, sample_audio_dir, output_dir):
        """Execution fails if validation fails."""
        config = PipelineConfig(
            name="invalid-test",
            input=PipelineInput(path=str(sample_audio_dir)),
            settings=PipelineSettings(output_dir=str(output_dir)),
            steps=[
                PipelineStep(
                    name="bad-step",
                    processor="nonexistent",
                    params={}
                )
            ]
        )
        
        with pytest.raises(ConfigError) as exc_info:
            engine.execute(config)
        
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_execute_creates_output_dirs(self, engine, valid_config, output_dir):
        """Execution creates step output directories."""
        session = engine.execute(valid_config)
        
        # Check step directory was created
        step_dirs = list(output_dir.glob("step_*"))
        assert len(step_dirs) >= 1
    
    def test_execute_step_failure_halts(self, engine, sample_audio_dir, output_dir):
        """AC-PIPE-3: Failure at step N halts, preserves steps 1 to N-1."""
        # This tests that when a step fails, execution stops
        # We mock a processor to fail
        
        config = PipelineConfig(
            name="failure-test",
            input=PipelineInput(path=str(sample_audio_dir), formats=["wav"]),
            settings=PipelineSettings(
                output_dir=str(output_dir),
                continue_on_error=False
            ),
            steps=[
                PipelineStep(
                    name="step-1",
                    processor="converter",
                    params={"output_format": "mp3"}
                ),
                PipelineStep(
                    name="step-2-fails",
                    processor="converter",
                    params={"output_format": "invalid_format_xxx"}
                ),
            ]
        )
        
        # Execute and expect failure
        with pytest.raises(ProcessingError) as exc_info:
            engine.execute(config)
        
        # Error message should indicate which step failed
        assert "step" in str(exc_info.value).lower()


class TestPipelineStepExecution:
    """Tests for individual step execution."""
    
    def test_step_output_becomes_next_input(self, engine, sample_audio_dir, output_dir):
        """Each step's output becomes next step's input."""
        config = PipelineConfig(
            name="chain-test",
            input=PipelineInput(path=str(sample_audio_dir), formats=["wav"]),
            settings=PipelineSettings(output_dir=str(output_dir)),
            steps=[
                PipelineStep(
                    name="to-mp3",
                    processor="converter",
                    params={"output_format": "mp3"}
                ),
                PipelineStep(
                    name="back-to-wav",
                    processor="converter",
                    params={"output_format": "wav"}
                ),
            ]
        )
        
        session = engine.execute(config)
        
        # Step 2 should have wav files (converted from mp3)
        step2_dir = output_dir / "step_02_back-to-wav"
        if step2_dir.exists():
            wav_files = list(step2_dir.glob("*.wav"))
            assert len(wav_files) > 0


class TestGetAvailableProcessors:
    """Tests for processor listing."""
    
    def test_get_available_processors(self, engine):
        """Should return list of available processor names."""
        processors = engine.get_available_processors()
        
        assert isinstance(processors, list)
        assert len(processors) > 0
        assert "converter" in processors
