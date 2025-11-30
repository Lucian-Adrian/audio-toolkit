"""Unit tests for pipeline configuration parsing."""

import pytest
from pathlib import Path
import tempfile

from pydantic import ValidationError

from src.core.exceptions import InvalidYAMLError, MissingParameterError
from src.orchestration.pipeline_config import (
    PipelineConfig,
    PipelineInput,
    PipelineSettings,
    PipelineStep,
    parse_pipeline_config,
    config_to_yaml,
)


class TestPipelineStep:
    """Tests for PipelineStep model."""
    
    def test_valid_step(self):
        """Create a valid pipeline step."""
        step = PipelineStep(
            name="convert-to-mp3",
            processor="converter",
            params={"output_format": "mp3"}
        )
        assert step.name == "convert-to-mp3"
        assert step.processor == "converter"
        assert step.params == {"output_format": "mp3"}
    
    def test_step_with_defaults(self):
        """Step with default empty params."""
        step = PipelineStep(name="test", processor="converter")
        assert step.params == {}
    
    def test_empty_name_raises(self):
        """Empty step name raises validation error."""
        with pytest.raises(ValidationError):
            PipelineStep(name="", processor="converter")
    
    def test_empty_processor_raises(self):
        """Empty processor name raises validation error."""
        with pytest.raises(ValidationError):
            PipelineStep(name="test", processor="")
    
    def test_whitespace_trimmed(self):
        """Whitespace is trimmed from name and processor."""
        step = PipelineStep(name="  test  ", processor="  converter  ")
        assert step.name == "test"
        assert step.processor == "converter"


class TestPipelineInput:
    """Tests for PipelineInput model."""
    
    def test_valid_input(self):
        """Create a valid pipeline input."""
        inp = PipelineInput(path="./audio")
        assert inp.path == "./audio"
        assert inp.recursive is True
        assert inp.formats == ["wav", "mp3", "flac"]
    
    def test_custom_formats(self):
        """Custom format list with normalization."""
        inp = PipelineInput(path="./audio", formats=[".WAV", "MP3", ".ogg"])
        assert inp.formats == ["wav", "mp3", "ogg"]
    
    def test_empty_path_raises(self):
        """Empty input path raises validation error."""
        with pytest.raises(ValidationError):
            PipelineInput(path="")


class TestPipelineSettings:
    """Tests for PipelineSettings model."""
    
    def test_default_settings(self):
        """Default settings are valid."""
        settings = PipelineSettings()
        assert settings.checkpoint_interval == 100
        assert settings.continue_on_error is False
        assert settings.output_dir == "./data/output"
    
    def test_custom_settings(self):
        """Custom settings are applied."""
        settings = PipelineSettings(
            checkpoint_interval=50,
            continue_on_error=True,
            output_dir="./custom/output"
        )
        assert settings.checkpoint_interval == 50
        assert settings.continue_on_error is True
        assert settings.output_dir == "./custom/output"
    
    def test_invalid_checkpoint_interval(self):
        """Checkpoint interval must be >= 1."""
        with pytest.raises(ValidationError):
            PipelineSettings(checkpoint_interval=0)


class TestPipelineConfig:
    """Tests for PipelineConfig model."""
    
    def test_valid_config(self):
        """Parse valid pipeline config."""
        config = PipelineConfig(
            name="test-pipeline",
            input=PipelineInput(path="./audio"),
            steps=[
                PipelineStep(name="step1", processor="converter")
            ]
        )
        assert config.name == "test-pipeline"
        assert config.version == "1.0"
        assert len(config.steps) == 1
    
    def test_empty_steps_raises(self):
        """Pipeline must have at least one step."""
        with pytest.raises(ValidationError) as exc_info:
            PipelineConfig(
                name="test",
                input=PipelineInput(path="./audio"),
                steps=[]
            )
        assert "at least one step" in str(exc_info.value).lower()
    
    def test_duplicate_step_names_raises(self):
        """Duplicate step names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PipelineConfig(
                name="test",
                input=PipelineInput(path="./audio"),
                steps=[
                    PipelineStep(name="same-name", processor="converter"),
                    PipelineStep(name="same-name", processor="splitter-fixed"),
                ]
            )
        assert "duplicate" in str(exc_info.value).lower()
    
    def test_empty_name_raises(self):
        """Empty pipeline name raises validation error."""
        with pytest.raises(ValidationError):
            PipelineConfig(
                name="",
                input=PipelineInput(path="./audio"),
                steps=[PipelineStep(name="step1", processor="converter")]
            )


class TestParseConfig:
    """Tests for parse_pipeline_config function."""
    
    def test_parse_valid_yaml(self, temp_dir):
        """Parse valid pipeline.yaml file."""
        config_content = """
name: test-pipeline
description: A test pipeline
version: "2.0"
settings:
  checkpoint_interval: 50
  continue_on_error: true
  output_dir: ./output
input:
  path: ./audio
  recursive: true
  formats:
    - wav
    - mp3
steps:
  - name: convert-step
    processor: converter
    params:
      output_format: mp3
"""
        config_path = temp_dir / "pipeline.yaml"
        config_path.write_text(config_content)
        
        config = parse_pipeline_config(config_path)
        
        assert config.name == "test-pipeline"
        assert config.description == "A test pipeline"
        assert config.version == "2.0"
        assert config.settings.checkpoint_interval == 50
        assert config.settings.continue_on_error is True
        assert config.input.path == "./audio"
        assert len(config.steps) == 1
        assert config.steps[0].name == "convert-step"
        assert config.steps[0].params["output_format"] == "mp3"
    
    def test_parse_invalid_yaml(self, temp_dir):
        """EC-PIPE-1: Invalid YAML raises InvalidYAMLError."""
        config_path = temp_dir / "bad.yaml"
        # Use actual invalid YAML syntax
        config_path.write_text("name: test\n  invalid: [unclosed bracket\n  bad: value")
        
        with pytest.raises(InvalidYAMLError):
            parse_pipeline_config(config_path)
    
    def test_parse_nonexistent_file(self, temp_dir):
        """Non-existent file raises InvalidYAMLError."""
        config_path = temp_dir / "nonexistent.yaml"
        
        with pytest.raises(InvalidYAMLError):
            parse_pipeline_config(config_path)
    
    def test_parse_empty_file(self, temp_dir):
        """Empty file raises InvalidYAMLError."""
        config_path = temp_dir / "empty.yaml"
        config_path.write_text("")
        
        with pytest.raises(InvalidYAMLError):
            parse_pipeline_config(config_path)
    
    def test_parse_missing_steps(self, temp_dir):
        """Raise error if steps is empty or missing."""
        config_content = """
name: test-pipeline
input:
  path: ./audio
steps: []
"""
        config_path = temp_dir / "no_steps.yaml"
        config_path.write_text(config_content)
        
        with pytest.raises(MissingParameterError):
            parse_pipeline_config(config_path)
    
    def test_parse_missing_required_fields(self, temp_dir):
        """Missing required fields raise MissingParameterError."""
        config_content = """
description: Missing name and input
steps:
  - name: step1
    processor: converter
"""
        config_path = temp_dir / "incomplete.yaml"
        config_path.write_text(config_content)
        
        with pytest.raises(MissingParameterError):
            parse_pipeline_config(config_path)


class TestConfigToYaml:
    """Tests for config_to_yaml function."""
    
    def test_roundtrip(self, temp_dir):
        """Config can be serialized and deserialized."""
        original = PipelineConfig(
            name="roundtrip-test",
            description="Test roundtrip",
            input=PipelineInput(path="./audio", formats=["wav"]),
            settings=PipelineSettings(checkpoint_interval=10),
            steps=[
                PipelineStep(
                    name="step1",
                    processor="converter",
                    params={"output_format": "mp3"}
                )
            ]
        )
        
        yaml_str = config_to_yaml(original)
        
        # Write to file and parse back
        config_path = temp_dir / "roundtrip.yaml"
        config_path.write_text(yaml_str)
        
        parsed = parse_pipeline_config(config_path)
        
        assert parsed.name == original.name
        assert parsed.description == original.description
        assert parsed.steps[0].name == original.steps[0].name
        assert parsed.steps[0].params == original.steps[0].params


# Fixture for temp directory
@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    import shutil
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)
