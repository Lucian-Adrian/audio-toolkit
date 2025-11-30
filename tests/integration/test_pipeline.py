"""Integration tests for pipeline execution."""

import pytest
from pathlib import Path
import tempfile
import shutil

from pydub.generators import Sine

from src.orchestration.pipeline import PipelineEngine
from src.orchestration.pipeline_config import (
    PipelineConfig,
    PipelineInput,
    PipelineSettings,
    PipelineStep,
    parse_pipeline_config,
)
from src.core.types import SessionStatus


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def audio_fixtures(temp_dir):
    """Create test audio fixtures."""
    audio_dir = temp_dir / "audio"
    audio_dir.mkdir()
    
    # Create 3 second audio files
    audio = Sine(440).to_audio_segment(duration=3000)
    
    for i in range(3):
        audio.export(str(audio_dir / f"test_{i+1}.wav"), format="wav")
    
    return audio_dir


@pytest.fixture
def output_dir(temp_dir):
    """Create output directory."""
    output = temp_dir / "output"
    output.mkdir()
    return output


class TestFullPipelineExecution:
    """Integration tests for complete pipeline execution."""
    
    def test_convert_pipeline(self, audio_fixtures, output_dir):
        """Execute: convert -> (verify outputs)."""
        engine = PipelineEngine()
        
        config = PipelineConfig(
            name="convert-pipeline",
            input=PipelineInput(
                path=str(audio_fixtures),
                formats=["wav"]
            ),
            settings=PipelineSettings(
                output_dir=str(output_dir),
                checkpoint_interval=10
            ),
            steps=[
                PipelineStep(
                    name="convert-to-mp3",
                    processor="converter",
                    params={"output_format": "mp3"}
                ),
            ]
        )
        
        session = engine.execute(config)
        
        # Verify session completed
        assert session.status == SessionStatus.COMPLETED
        
        # Verify outputs exist
        step_output = output_dir / "step_01_convert-to-mp3"
        assert step_output.exists()
        
        mp3_files = list(step_output.glob("*.mp3"))
        assert len(mp3_files) == 3  # Should have 3 MP3 files
    
    def test_multi_step_pipeline(self, audio_fixtures, output_dir):
        """Execute: convert to mp3 -> convert back to wav."""
        engine = PipelineEngine()
        
        config = PipelineConfig(
            name="multi-step-pipeline",
            input=PipelineInput(
                path=str(audio_fixtures),
                formats=["wav"]
            ),
            settings=PipelineSettings(
                output_dir=str(output_dir)
            ),
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
        
        assert session.status == SessionStatus.COMPLETED
        
        # Check both step outputs exist
        step1_output = output_dir / "step_01_to-mp3"
        step2_output = output_dir / "step_02_back-to-wav"
        
        assert step1_output.exists()
        assert step2_output.exists()
        
        # Step 1 should have mp3 files
        mp3_files = list(step1_output.glob("*.mp3"))
        assert len(mp3_files) == 3
        
        # Step 2 should have wav files
        wav_files = list(step2_output.glob("*.wav"))
        assert len(wav_files) == 3
    
    def test_pipeline_from_yaml_file(self, audio_fixtures, output_dir, temp_dir):
        """Parse and execute pipeline from YAML file."""
        yaml_content = f"""
name: yaml-pipeline
description: Test pipeline from YAML
version: "1.0"
settings:
  checkpoint_interval: 100
  continue_on_error: false
  output_dir: {str(output_dir)}
input:
  path: {str(audio_fixtures)}
  recursive: true
  formats:
    - wav
steps:
  - name: convert-to-mp3
    processor: converter
    params:
      output_format: mp3
"""
        
        config_path = temp_dir / "pipeline.yaml"
        config_path.write_text(yaml_content)
        
        # Parse and execute
        config = parse_pipeline_config(config_path)
        engine = PipelineEngine()
        session = engine.execute(config)
        
        assert session.status == SessionStatus.COMPLETED
        
        # Verify outputs
        step_output = output_dir / "step_01_convert-to-mp3"
        assert step_output.exists()
        assert len(list(step_output.glob("*.mp3"))) == 3
    
    def test_pipeline_with_split(self, audio_fixtures, output_dir):
        """Execute: convert -> split (tests processor chaining)."""
        engine = PipelineEngine()
        
        config = PipelineConfig(
            name="convert-split-pipeline",
            input=PipelineInput(
                path=str(audio_fixtures),
                formats=["wav"]
            ),
            settings=PipelineSettings(
                output_dir=str(output_dir)
            ),
            steps=[
                PipelineStep(
                    name="convert-to-mp3",
                    processor="converter",
                    params={"output_format": "mp3"}
                ),
                PipelineStep(
                    name="split-chunks",
                    processor="splitter-fixed",
                    params={"duration_ms": 1000}  # 1 second chunks (in ms)
                ),
            ]
        )
        
        session = engine.execute(config)
        
        assert session.status == SessionStatus.COMPLETED
        
        # Step 1 should have mp3 files
        step1_output = output_dir / "step_01_convert-to-mp3"
        assert len(list(step1_output.glob("*.mp3"))) == 3
        
        # Step 2 should have split segments
        step2_output = output_dir / "step_02_split-chunks"
        # Each 3-second file split into 1-second chunks = 9 segments total
        segments = list(step2_output.glob("*"))
        assert len(segments) >= 3  # At least 3 segments


class TestPipelineDryRunIntegration:
    """Integration tests for dry-run mode."""
    
    def test_dry_run_does_not_modify_files(self, audio_fixtures, output_dir):
        """Dry run should not create any output files."""
        engine = PipelineEngine()
        
        config = PipelineConfig(
            name="dry-run-test",
            input=PipelineInput(
                path=str(audio_fixtures),
                formats=["wav"]
            ),
            settings=PipelineSettings(
                output_dir=str(output_dir)
            ),
            steps=[
                PipelineStep(
                    name="convert",
                    processor="converter",
                    params={"output_format": "mp3"}
                ),
            ]
        )
        
        # Run dry-run
        plan = engine.dry_run(config)
        
        # Verify no outputs were created
        step_dirs = list(output_dir.glob("step_*"))
        assert len(step_dirs) == 0
        
        # But we should have a plan
        assert len(plan) > 0


class TestPipelineErrorHandling:
    """Integration tests for error handling."""
    
    def test_continue_on_error(self, audio_fixtures, output_dir, temp_dir):
        """With continue_on_error, pipeline continues despite failures."""
        # Create one corrupted file
        corrupted = audio_fixtures / "corrupted.wav"
        corrupted.write_text("not audio data")
        
        engine = PipelineEngine()
        
        config = PipelineConfig(
            name="error-handling-test",
            input=PipelineInput(
                path=str(audio_fixtures),
                formats=["wav"]
            ),
            settings=PipelineSettings(
                output_dir=str(output_dir),
                continue_on_error=True  # Should continue despite error
            ),
            steps=[
                PipelineStep(
                    name="convert",
                    processor="converter",
                    params={"output_format": "mp3"}
                ),
            ]
        )
        
        session = engine.execute(config)
        
        # Should complete (not fail entirely)
        assert session.status == SessionStatus.COMPLETED
        
        # Should have processed the valid files
        step_output = output_dir / "step_01_convert"
        mp3_files = list(step_output.glob("*.mp3"))
        assert len(mp3_files) >= 2  # At least the valid files


class TestPipelineValidationIntegration:
    """Integration tests for validation."""
    
    def test_validate_before_execute(self, audio_fixtures, output_dir):
        """Validate catches errors before any processing."""
        engine = PipelineEngine()
        
        config = PipelineConfig(
            name="validation-test",
            input=PipelineInput(
                path=str(audio_fixtures),
                formats=["wav"]
            ),
            settings=PipelineSettings(
                output_dir=str(output_dir)
            ),
            steps=[
                PipelineStep(
                    name="valid-step",
                    processor="converter",
                    params={"output_format": "mp3"}
                ),
            ]
        )
        
        errors = engine.validate(config)
        assert len(errors) == 0
        
        # Now test with invalid processor
        config.steps.append(
            PipelineStep(
                name="invalid",
                processor="does-not-exist",
                params={}
            )
        )
        
        errors = engine.validate(config)
        assert len(errors) > 0
