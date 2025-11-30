"""Pipeline configuration models using Pydantic."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from ..core.exceptions import InvalidYAMLError, MissingParameterError


class PipelineStep(BaseModel):
    """A single step in the pipeline."""
    
    name: str = Field(..., description="Unique name for this step")
    processor: str = Field(..., description="Processor name to execute")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the processor"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure step name is not empty."""
        if not v or not v.strip():
            raise ValueError("Step name cannot be empty")
        return v.strip()
    
    @field_validator("processor")
    @classmethod
    def validate_processor(cls, v: str) -> str:
        """Ensure processor name is not empty."""
        if not v or not v.strip():
            raise ValueError("Processor name cannot be empty")
        return v.strip()


class PipelineInput(BaseModel):
    """Input specification for the pipeline."""
    
    path: str = Field(..., description="Input path (file or directory)")
    recursive: bool = Field(
        default=True,
        description="Scan subdirectories recursively"
    )
    formats: List[str] = Field(
        default=["wav", "mp3", "flac"],
        description="Audio formats to process"
    )
    
    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Ensure path is not empty."""
        if not v or not v.strip():
            raise ValueError("Input path cannot be empty")
        return v.strip()
    
    @field_validator("formats")
    @classmethod
    def validate_formats(cls, v: List[str]) -> List[str]:
        """Normalize format extensions."""
        return [fmt.lower().lstrip(".") for fmt in v]


class PipelineSettings(BaseModel):
    """Global pipeline settings."""
    
    checkpoint_interval: int = Field(
        default=100,
        ge=1,
        description="Files between checkpoints"
    )
    continue_on_error: bool = Field(
        default=False,
        description="Continue on step failure"
    )
    output_dir: str = Field(
        default="./data/output",
        description="Output directory for results"
    )
    
    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: str) -> str:
        """Ensure output dir is not empty."""
        if not v or not v.strip():
            raise ValueError("Output directory cannot be empty")
        return v.strip()


class PipelineConfig(BaseModel):
    """Complete pipeline configuration."""
    
    name: str = Field(..., description="Pipeline name")
    description: str = Field(default="", description="Pipeline description")
    version: str = Field(default="1.0", description="Pipeline version")
    settings: PipelineSettings = Field(default_factory=PipelineSettings)
    input: PipelineInput
    steps: List[PipelineStep]
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure pipeline name is not empty."""
        if not v or not v.strip():
            raise ValueError("Pipeline name cannot be empty")
        return v.strip()
    
    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: List[PipelineStep]) -> List[PipelineStep]:
        """Ensure pipeline has at least one step."""
        if not v:
            raise ValueError("Pipeline must have at least one step")
        return v
    
    @model_validator(mode="after")
    def validate_unique_step_names(self) -> "PipelineConfig":
        """Ensure all step names are unique."""
        names = [step.name for step in self.steps]
        if len(names) != len(set(names)):
            duplicates = [n for n in names if names.count(n) > 1]
            raise ValueError(f"Duplicate step names: {set(duplicates)}")
        return self


def parse_pipeline_config(config_path: Path) -> PipelineConfig:
    """
    Parse a pipeline configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Validated PipelineConfig object
        
    Raises:
        InvalidYAMLError: If YAML parsing fails
        MissingParameterError: If required fields are missing
    """
    if not config_path.exists():
        raise InvalidYAMLError(f"Config file not found: {config_path}")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise InvalidYAMLError(f"Invalid YAML syntax: {e}") from e
    
    if raw_config is None:
        raise InvalidYAMLError("Empty configuration file")
    
    if not isinstance(raw_config, dict):
        raise InvalidYAMLError("Configuration must be a YAML mapping")
    
    try:
        return PipelineConfig.model_validate(raw_config)
    except Exception as e:
        raise MissingParameterError(f"Invalid pipeline config: {e}") from e


def config_to_yaml(config: PipelineConfig) -> str:
    """
    Convert a pipeline config back to YAML string.
    
    Args:
        config: PipelineConfig object
        
    Returns:
        YAML string representation
    """
    return yaml.dump(
        config.model_dump(),
        default_flow_style=False,
        sort_keys=False
    )
