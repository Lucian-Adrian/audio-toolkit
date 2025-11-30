"""Tests for pipeline CLI commands."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from src.presentation.cli.pipeline_cmd import app


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_pipeline_yaml(tmp_path):
    """Create a sample pipeline YAML file."""
    yaml_content = """
name: test-pipeline
version: "1.0"
description: Test pipeline

input:
  path: ./input
  recursive: false
  formats:
    - mp3
    - wav

settings:
  output_dir: ./output
  checkpoint_interval: 10
  continue_on_error: false

steps:
  - name: convert-step
    processor: converter
    params:
      output_format: wav
"""
    yaml_file = tmp_path / "test_pipeline.yaml"
    yaml_file.write_text(yaml_content)
    return yaml_file


class TestRunPipeline:
    """Tests for pipeline run command."""
    
    @patch("src.presentation.cli.pipeline_cmd.PipelineEngine")
    @patch("src.presentation.cli.pipeline_cmd.parse_pipeline_config")
    def test_run_dry_run(self, mock_parse, mock_engine_class, runner, sample_pipeline_yaml):
        """Test running pipeline in dry-run mode."""
        # Setup mocks
        mock_config = Mock()
        mock_config.name = "test-pipeline"
        mock_config.steps = []
        mock_parse.return_value = mock_config
        
        mock_engine = Mock()
        mock_engine.validate.return_value = []  # No errors
        mock_engine.dry_run.return_value = None
        mock_engine_class.return_value = mock_engine
        
        result = runner.invoke(app, ["run", "--config", str(sample_pipeline_yaml), "--dry-run"])
        
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "valid" in result.output.lower()
    
    @patch("src.presentation.cli.pipeline_cmd.PipelineEngine")
    @patch("src.presentation.cli.pipeline_cmd.parse_pipeline_config")
    def test_run_dry_run_with_validation_errors(self, mock_parse, mock_engine_class, runner, sample_pipeline_yaml):
        """Test dry-run with validation errors."""
        mock_config = Mock()
        mock_config.name = "test-pipeline"
        mock_config.steps = []
        mock_parse.return_value = mock_config
        
        mock_engine = Mock()
        mock_engine.validate.return_value = ["Error 1", "Error 2"]
        mock_engine.dry_run.return_value = None
        mock_engine_class.return_value = mock_engine
        
        result = runner.invoke(app, ["run", "--config", str(sample_pipeline_yaml), "--dry-run"])
        
        assert result.exit_code == 1
        assert "Validation Errors" in result.output
    
    @patch("src.presentation.cli.pipeline_cmd.PipelineEngine")
    @patch("src.presentation.cli.pipeline_cmd.parse_pipeline_config")
    def test_run_execute(self, mock_parse, mock_engine_class, runner, sample_pipeline_yaml):
        """Test executing a pipeline."""
        mock_config = Mock()
        mock_config.name = "test-pipeline"
        mock_config.steps = [Mock()]
        mock_parse.return_value = mock_config
        
        mock_session = Mock()
        mock_session.session_id = "test-session-123"
        mock_session.total_files = 10
        mock_session.processed_count = 10
        mock_session.failed_count = 0
        
        mock_engine = Mock()
        mock_engine.execute.return_value = mock_session
        mock_engine_class.return_value = mock_engine
        
        result = runner.invoke(app, ["run", "--config", str(sample_pipeline_yaml)])
        
        assert result.exit_code == 0
        assert "Pipeline Complete" in result.output
        assert "test-session-123" in result.output
    
    @patch("src.presentation.cli.pipeline_cmd.parse_pipeline_config")
    def test_run_invalid_yaml(self, mock_parse, runner, sample_pipeline_yaml):
        """Test running with invalid YAML."""
        from src.core.exceptions import InvalidYAMLError
        mock_parse.side_effect = InvalidYAMLError("Invalid YAML syntax")
        
        result = runner.invoke(app, ["run", "--config", str(sample_pipeline_yaml)])
        
        assert result.exit_code == 1
        assert "Invalid YAML" in result.output
    
    @patch("src.presentation.cli.pipeline_cmd.parse_pipeline_config")
    def test_run_config_error(self, mock_parse, runner, sample_pipeline_yaml):
        """Test running with config error."""
        from src.core.exceptions import ConfigError
        mock_parse.side_effect = ConfigError("Missing required field")
        
        result = runner.invoke(app, ["run", "--config", str(sample_pipeline_yaml)])
        
        assert result.exit_code == 1
        assert "Configuration Error" in result.output
    
    @patch("src.presentation.cli.pipeline_cmd.PipelineEngine")
    @patch("src.presentation.cli.pipeline_cmd.parse_pipeline_config")
    def test_run_processing_error(self, mock_parse, mock_engine_class, runner, sample_pipeline_yaml):
        """Test running with processing error."""
        from src.core.exceptions import ProcessingError
        
        mock_config = Mock()
        mock_config.name = "test-pipeline"
        mock_config.steps = [Mock()]
        mock_parse.return_value = mock_config
        
        mock_engine = Mock()
        mock_engine.execute.side_effect = ProcessingError("Processing failed")
        mock_engine_class.return_value = mock_engine
        
        result = runner.invoke(app, ["run", "--config", str(sample_pipeline_yaml)])
        
        assert result.exit_code == 1
        assert "Processing Error" in result.output
    
    @patch("src.presentation.cli.pipeline_cmd.PipelineEngine")
    @patch("src.presentation.cli.pipeline_cmd.parse_pipeline_config")
    def test_run_with_resume(self, mock_parse, mock_engine_class, runner, sample_pipeline_yaml):
        """Test running pipeline with resume flag."""
        mock_config = Mock()
        mock_config.name = "test-pipeline"
        mock_config.steps = [Mock()]
        mock_parse.return_value = mock_config
        
        mock_session = Mock()
        mock_session.session_id = "test-session-123"
        mock_session.total_files = 10
        mock_session.processed_count = 10
        mock_session.failed_count = 0
        
        mock_engine = Mock()
        mock_engine.execute.return_value = mock_session
        mock_engine_class.return_value = mock_engine
        
        result = runner.invoke(app, ["run", "--config", str(sample_pipeline_yaml), "--resume"])
        
        mock_engine.execute.assert_called_once_with(
            config=mock_config,
            resume=True,
            resume_from_step=None,
        )
    
    @patch("src.presentation.cli.pipeline_cmd.PipelineEngine")
    @patch("src.presentation.cli.pipeline_cmd.parse_pipeline_config")
    def test_run_with_resume_from(self, mock_parse, mock_engine_class, runner, sample_pipeline_yaml):
        """Test running pipeline with resume-from step."""
        mock_config = Mock()
        mock_config.name = "test-pipeline"
        mock_config.steps = [Mock(), Mock()]
        mock_parse.return_value = mock_config
        
        mock_session = Mock()
        mock_session.session_id = "test-session-123"
        mock_session.total_files = 10
        mock_session.processed_count = 10
        mock_session.failed_count = 0
        
        mock_engine = Mock()
        mock_engine.execute.return_value = mock_session
        mock_engine_class.return_value = mock_engine
        
        result = runner.invoke(app, ["run", "--config", str(sample_pipeline_yaml), "--resume-from", "2"])
        
        mock_engine.execute.assert_called_once_with(
            config=mock_config,
            resume=False,
            resume_from_step=2,
        )
    
    def test_run_config_not_found(self, runner, tmp_path):
        """Test running with non-existent config file."""
        result = runner.invoke(app, ["run", "--config", str(tmp_path / "nonexistent.yaml")])
        
        assert result.exit_code != 0


class TestValidatePipeline:
    """Tests for pipeline validate command."""
    
    @patch("src.presentation.cli.pipeline_cmd.PipelineEngine")
    @patch("src.presentation.cli.pipeline_cmd.parse_pipeline_config")
    def test_validate_success(self, mock_parse, mock_engine_class, runner, sample_pipeline_yaml):
        """Test validating a valid pipeline."""
        mock_step = Mock()
        mock_step.name = "convert-step"
        mock_step.processor = "converter"
        mock_step.params = {"output_format": "wav"}
        
        mock_input = Mock()
        mock_input.path = "./input"
        
        mock_settings = Mock()
        mock_settings.output_dir = "./output"
        
        mock_config = Mock()
        mock_config.name = "test-pipeline"
        mock_config.version = "1.0"
        mock_config.steps = [mock_step]
        mock_config.input = mock_input
        mock_config.settings = mock_settings
        mock_parse.return_value = mock_config
        
        mock_engine = Mock()
        mock_engine.validate.return_value = []  # No errors
        mock_engine_class.return_value = mock_engine
        
        result = runner.invoke(app, ["validate", "--config", str(sample_pipeline_yaml)])
        
        assert result.exit_code == 0
        assert "valid" in result.output.lower()
        assert "test-pipeline" in result.output
    
    @patch("src.presentation.cli.pipeline_cmd.PipelineEngine")
    @patch("src.presentation.cli.pipeline_cmd.parse_pipeline_config")
    def test_validate_with_errors(self, mock_parse, mock_engine_class, runner, sample_pipeline_yaml):
        """Test validating an invalid pipeline."""
        mock_config = Mock()
        mock_config.name = "test-pipeline"
        mock_config.steps = []
        mock_parse.return_value = mock_config
        
        mock_engine = Mock()
        mock_engine.validate.return_value = ["Unknown processor: invalid", "Missing required param: x"]
        mock_engine_class.return_value = mock_engine
        
        result = runner.invoke(app, ["validate", "--config", str(sample_pipeline_yaml)])
        
        assert result.exit_code == 1
        assert "Validation Failed" in result.output
        assert "Unknown processor" in result.output
    
    @patch("src.presentation.cli.pipeline_cmd.parse_pipeline_config")
    def test_validate_invalid_yaml(self, mock_parse, runner, sample_pipeline_yaml):
        """Test validating with invalid YAML."""
        from src.core.exceptions import InvalidYAMLError
        mock_parse.side_effect = InvalidYAMLError("Syntax error")
        
        result = runner.invoke(app, ["validate", "--config", str(sample_pipeline_yaml)])
        
        assert result.exit_code == 1
        assert "Invalid YAML" in result.output


class TestListProcessors:
    """Tests for pipeline processors command."""
    
    @patch("src.presentation.cli.pipeline_cmd.list_processors")
    def test_list_processors(self, mock_list, runner):
        """Test listing available processors."""
        from src.core.types import ProcessorCategory
        
        # The actual implementation uses get_processor from processors module
        # Just verify the command runs and outputs table
        mock_list.return_value = []
        
        result = runner.invoke(app, ["processors"])
        
        assert result.exit_code == 0
        assert "Available Processors" in result.output
    
    @patch("src.processors.get_processor")
    @patch("src.presentation.cli.pipeline_cmd.list_processors")
    def test_list_processors_with_data(self, mock_list, mock_get, runner):
        """Test listing processors with actual data."""
        from src.core.types import ProcessorCategory
        
        mock_list.return_value = ["converter"]
        
        mock_converter = Mock()
        mock_converter.name = "converter"
        mock_converter.version = "1.0.0"
        mock_converter.description = "Convert audio formats"
        mock_converter.category = ProcessorCategory.MANIPULATION
        
        mock_get.return_value = mock_converter
        
        result = runner.invoke(app, ["processors"])
        
        assert result.exit_code == 0
        assert "converter" in result.output


class TestNoArgsHelp:
    """Test that no args shows help."""
    
    def test_no_args_shows_help(self, runner):
        """Test that running without args shows help."""
        result = runner.invoke(app, [])
        
        # no_args_is_help=True returns exit code 2 in typer
        assert result.exit_code == 2
        assert "Usage" in result.output or "pipeline" in result.output.lower()
