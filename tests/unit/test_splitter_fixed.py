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
        assert "min_last_segment_ms" in param_names
        assert "crossfade_ms" in param_names
        
        # Check duration_ms has proper constraints
        duration_param = next(p for p in params if p.name == "duration_ms")
        assert duration_param.required is True
        assert duration_param.min_value == 100.0
        assert duration_param.max_value == FixedSplitter.MAX_DURATION_MS
    
    def test_max_duration_constant(self):
        """Test MAX_DURATION_MS constant is 1 hour."""
        assert FixedSplitter.MAX_DURATION_MS == 3_600_000.0


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
    
    def test_split_metadata_complete(self, sample_audio_10sec, output_dir):
        """Test complete metadata in result."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=sample_audio_10sec,
            output_dir=output_dir,
            duration_ms=2000.0,
            output_format="wav",
        )
        
        assert result.success is True
        # Required metadata
        assert "segment_count" in result.metadata
        assert "duration_ms" in result.metadata
        assert "total_duration_ms" in result.metadata
        assert result.metadata["duration_ms"] == 2000.0
        
        # New enhanced metadata
        assert "avg_segment_ms" in result.metadata
        assert "output_format" in result.metadata
        assert "input_format" in result.metadata
        assert "processor" in result.metadata
        assert "version" in result.metadata
        assert result.metadata["processor"] == "splitter-fixed"
        assert result.metadata["output_format"] == "wav"
    
    def test_split_short_file_single_segment(self, sample_audio_5sec, output_dir):
        """Test splitting file shorter than duration creates single segment."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            duration_ms=10000.0,  # 10s > 5s file
            output_format="wav",
        )
        
        assert result.success is True
        assert len(result.output_paths) == 1
        assert result.metadata["segment_count"] == 1


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


class TestFixedSplitterMinLastSegment:
    """Test min_last_segment_ms behavior."""
    
    def test_short_remainder_merged(self, sample_audio_10sec, output_dir):
        """Test that short remainder is merged with previous segment."""
        splitter = FixedSplitter()
        
        # 10s / 3s = 3 segments (3s, 3s, 3s) + 1s remainder
        # With min_last_segment_ms=2000, the 1s gets merged with last segment
        result = splitter.process(
            input_path=sample_audio_10sec,
            output_dir=output_dir,
            duration_ms=3000.0,
            output_format="wav",
            min_last_segment_ms=2000.0,
        )
        
        assert result.success is True
        # Should be 3 segments: 3s, 3s, 4s (merged)
        assert len(result.output_paths) == 3
    
    def test_zero_min_last_segment(self, sample_audio_10sec, output_dir):
        """Test with min_last_segment_ms=0 (no merging)."""
        splitter = FixedSplitter()
        
        result = splitter.process(
            input_path=sample_audio_10sec,
            output_dir=output_dir,
            duration_ms=3000.0,
            output_format="wav",
            min_last_segment_ms=0.0,  # No merging
        )
        
        assert result.success is True
        # Should be 4 segments: 3s, 3s, 3s, 1s
        assert len(result.output_paths) == 4


class TestProcessorRegistry:
    """Test processor registry integration."""
    
    def test_get_processor_by_name(self):
        """Test getting FixedSplitter from registry."""
        processor = get_processor("splitter-fixed")
        
        assert isinstance(processor, FixedSplitter)
        assert processor.name == "splitter-fixed"


class TestFixedSplitterPureFunction:
    """Test that FixedSplitter is a pure function."""
    
    def test_no_state_between_calls(self, sample_audio_5sec, output_dir):
        """Test that processor maintains no state between process calls."""
        splitter = FixedSplitter()
        
        # First call
        result1 = splitter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir / "run1",
            duration_ms=1000.0,
            output_format="wav",
        )
        
        # Second call
        result2 = splitter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir / "run2",
            duration_ms=2000.0,
            output_format="mp3",
        )
        
        # Both should succeed independently
        assert result1.success is True
        assert result2.success is True
        
        # Results should be independent
        assert len(result1.output_paths) != len(result2.output_paths)
        assert result1.output_paths[0].suffix == ".wav"
        assert result2.output_paths[0].suffix == ".mp3"
