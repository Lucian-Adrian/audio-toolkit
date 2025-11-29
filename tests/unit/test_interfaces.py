"""Unit tests for interfaces."""

import pytest
from unittest.mock import Mock, MagicMock
from src.core.interfaces import AudioProcessor, AudioSplitter, AudioValidator, ProgressReporter
from src.core.types import AudioFile, ProcessingConfig, SplitConfig, ConversionResult, SplitResult
from pathlib import Path


class TestAudioProcessor:
    """Test AudioProcessor interface."""

    def test_abstract_methods(self):
        """Test that AudioProcessor has abstract methods."""
        # Can't instantiate abstract class directly
        with pytest.raises(TypeError):
            AudioProcessor()

        # Create a concrete implementation
        class ConcreteProcessor(AudioProcessor):
            def process(self, audio_file, config):
                return ConversionResult(
                    input_file=audio_file,
                    output_file=audio_file,
                    success=True
                )

        processor = ConcreteProcessor()
        assert isinstance(processor, AudioProcessor)


class TestAudioSplitter:
    """Test AudioSplitter interface."""

    def test_abstract_methods(self):
        """Test that AudioSplitter has abstract methods."""
        with pytest.raises(TypeError):
            AudioSplitter()

        class ConcreteSplitter(AudioSplitter):
            def split(self, audio_file, config):
                return SplitResult(
                    input_file=audio_file,
                    output_files=[],
                    success=True
                )

        splitter = ConcreteSplitter()
        assert isinstance(splitter, AudioSplitter)


class TestAudioValidator:
    """Test AudioValidator interface."""

    def test_abstract_methods(self):
        """Test that AudioValidator has abstract methods."""
        with pytest.raises(TypeError):
            AudioValidator()

        class ConcreteValidator(AudioValidator):
            def validate(self, audio_file):
                return True

            def get_validation_errors(self, audio_file):
                return []

        validator = ConcreteValidator()
        assert isinstance(validator, AudioValidator)


class TestProgressReporter:
    """Test ProgressReporter interface."""

    def test_abstract_methods(self):
        """Test that ProgressReporter has abstract methods."""
        with pytest.raises(TypeError):
            ProgressReporter()

        class ConcreteReporter(ProgressReporter):
            def start(self, total_steps, description=""):
                pass

            def update(self, current_step):
                pass

            def complete(self):
                pass

        reporter = ConcreteReporter()
        assert isinstance(reporter, ProgressReporter)