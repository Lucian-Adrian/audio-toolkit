"""Unit tests for the FixedSplitter processor."""

import pytest
from pathlib import Path

from src.processors import FixedSplitter, get_processor
from src.core.types import ProcessorCategory


class TestFixedSplitterProperties:
    """Test FixedSplitter properties."""
    
    def test_name(self):
        """Test processor name."""
        splitter = FixedSplitter()
        assert splitter.name == "splitter-fixed"
    
    def test_version(self):
        """Test processor version."""
        splitter = FixedSplitter()
        assert splitter.version == "1.0.0"
    
    def test_description(self):
        """Test processor description."""
        splitter = FixedSplitter()
        assert "fixed-duration" in splitter.description.lower()
    
    def test_category(self):
        """Test processor category."""
        splitter = FixedSplitter()
        assert splitter.category == ProcessorCategory.MANIPULATION
    
    def test_parameters(self):
        """Test processor parameters."""
        splitter = FixedSplitter()
        params = splitter.parameters
        
        # Check required parameters exist
        param_names = [p.name for p in params]
        assert "duration_ms" in param_names
        assert "output_format" in param_names
        
        # Check duration_ms is required
        duration_param = next(p for p in params if p.name == "duration_ms")
        assert duration_param.required is True
        assert duration_param.min_value == 100.0


class TestFixedSplitterProcess:
    """Test FixedSplitter.process() method."""
    
    def test_split_exact_segments(self, sample_audio_10sec, output_dir):
        """Test splitting into exact segments."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=sample_audio_10sec,
            output_dir=output_dir,
            duration_ms=2000.0,
            output_format="wav",
        )
        
        assert result.success is True
        assert len(result.output_paths) == 5
        assert result.metadata["segment_count"] == 5
        
        # Check files exist
        for path in result.output_paths:
            assert path.exists()
            assert path.suffix == ".wav"
    
    def test_split_with_remainder(self, sample_audio_10sec, output_dir):
        """Test splitting with remainder segment."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=sample_audio_10sec,
            output_dir=output_dir,
            duration_ms=3000.0,
            output_format="mp3",
        )
        
        assert result.success is True
        # 10s / 3s = 3 full + 1s remainder
        # With cleanup, the 1s remainder gets merged with previous
        assert len(result.output_paths) >= 3
    
    def test_split_output_format(self, sample_audio_5sec, output_dir):
        """Test output format conversion."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            duration_ms=2000.0,
            output_format="mp3",
        )
        
        assert result.success is True
        for path in result.output_paths:
            assert path.suffix == ".mp3"
    
    def test_split_creates_output_dir(self, sample_audio_5sec, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        splitter = FixedSplitter()
        new_output_dir = temp_dir / "new_output"
        
        assert not new_output_dir.exists()
        
        result = splitter.process(
            input_path=sample_audio_5sec,
            output_dir=new_output_dir,
            duration_ms=1000.0,
            output_format="wav",
        )
        
        assert result.success is True
        assert new_output_dir.exists()
    
    def test_split_nonexistent_file(self, temp_dir, output_dir):
        """Test splitting nonexistent file returns failure."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=temp_dir / "nonexistent.wav",
            output_dir=output_dir,
            duration_ms=1000.0,
            output_format="wav",
        )
        
        assert result.success is False
        assert "not found" in result.error_message.lower()
    
    def test_split_empty_file(self, empty_file, output_dir):
        """Test splitting empty file returns failure."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=empty_file,
            output_dir=output_dir,
            duration_ms=1000.0,
            output_format="wav",
        )
        
        assert result.success is False
        assert "empty" in result.error_message.lower()
    
    def test_split_invalid_duration(self, sample_audio_5sec, output_dir):
        """Test splitting with invalid duration returns failure."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            duration_ms=10.0,  # Too short
            output_format="wav",
        )
        
        assert result.success is False
        assert "duration" in result.error_message.lower()
    
    def test_split_processing_time_recorded(self, sample_audio_5sec, output_dir):
        """Test that processing time is recorded."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            duration_ms=1000.0,
            output_format="wav",
        )
        
        assert result.success is True
        assert result.processing_time_ms > 0
    
    def test_split_metadata(self, sample_audio_10sec, output_dir):
        """Test metadata in result."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=sample_audio_10sec,
            output_dir=output_dir,
            duration_ms=2000.0,
            output_format="wav",
        )
        
        assert result.success is True
        assert "segment_count" in result.metadata
        assert "duration_ms" in result.metadata
        assert "total_duration_ms" in result.metadata
        assert result.metadata["duration_ms"] == 2000.0


class TestFixedSplitterSegmentFilenames:
    """Test segment filename generation."""
    
    def test_segment_filename_format(self, sample_audio_5sec, output_dir):
        """Test segment filename format."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            duration_ms=1000.0,
            output_format="wav",
        )
        
        assert result.success is True
        
        # Check filename pattern: {stem}_segment_{NNN}.{ext}
        for i, path in enumerate(result.output_paths, 1):
            expected_name = f"{sample_audio_5sec.stem}_segment_{i:03d}.wav"
            assert path.name == expected_name


class TestProcessorRegistry:
    """Test processor registry integration."""
    
    def test_get_processor_by_name(self):
        """Test getting FixedSplitter from registry."""
        processor = get_processor("splitter-fixed")
        
        assert isinstance(processor, FixedSplitter)
        assert processor.name == "splitter-fixed"
