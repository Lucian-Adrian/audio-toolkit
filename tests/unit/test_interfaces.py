"""Unit tests for core interfaces."""

import pytest
from pathlib import Path
from typing import List

from src.core.interfaces import AudioProcessor
from src.core.types import ParameterSpec, ProcessorCategory, ProcessResult


class ConcreteProcessor(AudioProcessor):
    """Concrete implementation for testing."""
    
    @property
    def name(self) -> str:
        return "test-processor"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Test processor"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.CORE
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec(
                name="required_param",
                type="string",
                description="A required parameter",
                required=True,
            ),
            ParameterSpec(
                name="optional_param",
                type="integer",
                description="An optional parameter",
                required=False,
                default=10,
                min_value=1,
                max_value=100,
            ),
        ]
    
    def process(self, input_path: Path, output_dir: Path, **kwargs) -> ProcessResult:
        return ProcessResult(success=True, input_path=input_path)


class TestAudioProcessorValidateParams:
    """Tests for AudioProcessor.validate_params method."""
    
    def test_validate_params_missing_required(self):
        """Test validation catches missing required parameter."""
        processor = ConcreteProcessor()
        errors = processor.validate_params()
        
        assert len(errors) == 1
        assert "required_param" in errors[0]
        assert "Missing" in errors[0]
    
    def test_validate_params_all_valid(self):
        """Test validation passes with all valid params."""
        processor = ConcreteProcessor()
        errors = processor.validate_params(required_param="value", optional_param=50)
        
        assert errors == []
    
    def test_validate_params_below_min(self):
        """Test validation catches value below minimum."""
        processor = ConcreteProcessor()
        errors = processor.validate_params(required_param="value", optional_param=0)
        
        assert len(errors) == 1
        assert "optional_param" in errors[0]
        assert ">=" in errors[0]
    
    def test_validate_params_above_max(self):
        """Test validation catches value above maximum."""
        processor = ConcreteProcessor()
        errors = processor.validate_params(required_param="value", optional_param=150)
        
        assert len(errors) == 1
        assert "optional_param" in errors[0]
        assert "<=" in errors[0]
    
    def test_validate_params_multiple_errors(self):
        """Test validation returns multiple errors."""
        processor = ConcreteProcessor()
        # Missing required and invalid optional
        errors = processor.validate_params(optional_param=0)
        
        assert len(errors) == 2
