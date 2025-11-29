"""Unit tests for the FormatConverter processor."""

import pytest
from pathlib import Path

from src.processors import FormatConverter, get_processor
from src.core.types import ProcessorCategory


class TestFormatConverterProperties:
    """Test FormatConverter properties."""
    
    def test_name(self):
        """Test processor name."""
        converter = FormatConverter()
        assert converter.name == "converter"
    
    def test_version(self):
        """Test processor version."""
        converter = FormatConverter()
        assert converter.version == "1.0.0"
    
    def test_description(self):
        """Test processor description."""
        converter = FormatConverter()
        assert "convert" in converter.description.lower()
    
    def test_category(self):
        """Test processor category."""
        converter = FormatConverter()
        assert converter.category == ProcessorCategory.MANIPULATION
    
    def test_parameters(self):
        """Test processor parameters."""
        converter = FormatConverter()
        params = converter.parameters
        
        param_names = [p.name for p in params]
        assert "output_format" in param_names
        assert "bitrate" in param_names
        assert "normalize_audio" in param_names
        assert "sample_rate" in param_names
        assert "channels" in param_names


class TestFormatConverterProcess:
    """Test FormatConverter.process() method."""
    
    def test_convert_wav_to_mp3(self, sample_audio_5sec, output_dir):
        """Test converting WAV to MP3."""
        converter = FormatConverter()
        
        result = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            output_format="mp3",
        )
        
        assert result.success is True
        assert len(result.output_paths) == 1
        assert result.output_paths[0].suffix == ".mp3"
        assert result.output_paths[0].exists()
    
    def test_convert_wav_to_flac(self, sample_audio_5sec, output_dir):
        """Test converting WAV to FLAC."""
        converter = FormatConverter()
        
        result = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            output_format="flac",
        )
        
        assert result.success is True
        assert result.output_paths[0].suffix == ".flac"
    
    def test_convert_with_normalize(self, sample_audio_5sec, output_dir):
        """Test conversion with normalization."""
        converter = FormatConverter()
        
        result = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            output_format="mp3",
            normalize_audio=True,
        )
        
        assert result.success is True
        assert result.metadata.get("normalized") is True
    
    def test_convert_creates_output_dir(self, sample_audio_5sec, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        converter = FormatConverter()
        new_output_dir = temp_dir / "new_conversion_output"
        
        assert not new_output_dir.exists()
        
        result = converter.process(
            input_path=sample_audio_5sec,
            output_dir=new_output_dir,
            output_format="mp3",
        )
        
        assert result.success is True
        assert new_output_dir.exists()
    
    def test_convert_nonexistent_file(self, temp_dir, output_dir):
        """Test converting nonexistent file returns failure."""
        converter = FormatConverter()
        
        result = converter.process(
            input_path=temp_dir / "nonexistent.wav",
            output_dir=output_dir,
            output_format="mp3",
        )
        
        assert result.success is False
        assert "not found" in result.error_message.lower()
    
    def test_convert_unsupported_format(self, sample_audio_5sec, output_dir):
        """Test converting to unsupported format returns failure."""
        converter = FormatConverter()
        
        result = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            output_format="xyz",
        )
        
        assert result.success is False
        assert "unsupported" in result.error_message.lower()
    
    def test_convert_processing_time_recorded(self, sample_audio_5sec, output_dir):
        """Test that processing time is recorded."""
        converter = FormatConverter()
        
        result = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            output_format="mp3",
        )
        
        assert result.success is True
        assert result.processing_time_ms > 0
    
    def test_convert_metadata_complete(self, sample_audio_5sec, output_dir):
        """Test complete metadata in result."""
        converter = FormatConverter()
        
        result = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            output_format="mp3",
        )
        
        assert result.success is True
        # Required metadata
        assert "input_format" in result.metadata
        assert "output_format" in result.metadata
        assert result.metadata["output_format"] == "mp3"
        
        # New enhanced metadata
        assert "input_sample_rate" in result.metadata
        assert "output_sample_rate" in result.metadata
        assert "input_channels" in result.metadata
        assert "output_channels" in result.metadata
        assert "input_duration_ms" in result.metadata
        assert "output_duration_ms" in result.metadata
        assert "processor" in result.metadata
        assert "version" in result.metadata
        assert result.metadata["processor"] == "converter"


class TestFormatConverterSampleRate:
    """Test sample rate conversion."""
    
    def test_convert_with_sample_rate(self, sample_audio_5sec, output_dir):
        """Test conversion with sample rate change."""
        converter = FormatConverter()
        
        result = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            output_format="wav",
            sample_rate=22050,
        )
        
        assert result.success is True
        assert result.metadata["output_sample_rate"] == 22050
    
    def test_convert_preserve_sample_rate(self, sample_audio_5sec, output_dir):
        """Test conversion preserves sample rate when not specified."""
        converter = FormatConverter()
        
        result = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            output_format="wav",
            sample_rate=None,  # Preserve
        )
        
        assert result.success is True
        assert result.metadata["input_sample_rate"] == result.metadata["output_sample_rate"]


class TestFormatConverterChannels:
    """Test channel conversion."""
    
    def test_convert_to_mono(self, sample_audio_5sec, output_dir):
        """Test conversion to mono."""
        converter = FormatConverter()
        
        result = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            output_format="wav",
            channels=1,
        )
        
        assert result.success is True
        assert result.metadata["output_channels"] == 1


class TestFormatConverterOutputFilename:
    """Test output filename generation."""
    
    def test_output_filename_preserves_stem(self, sample_audio_5sec, output_dir):
        """Test output filename preserves original stem."""
        converter = FormatConverter()
        
        result = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir,
            output_format="mp3",
        )
        
        assert result.success is True
        output_stem = result.output_paths[0].stem
        assert output_stem == sample_audio_5sec.stem


class TestConverterRegistry:
    """Test processor registry integration."""
    
    def test_get_processor_by_name(self):
        """Test getting FormatConverter from registry."""
        processor = get_processor("converter")
        
        assert isinstance(processor, FormatConverter)
        assert processor.name == "converter"


class TestFormatConverterPureFunction:
    """Test that FormatConverter is a pure function."""
    
    def test_no_state_between_calls(self, sample_audio_5sec, output_dir):
        """Test that processor maintains no state between process calls."""
        converter = FormatConverter()
        
        # First call with normalization
        result1 = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir / "run1",
            output_format="mp3",
            normalize_audio=True,
        )
        
        # Second call without normalization
        result2 = converter.process(
            input_path=sample_audio_5sec,
            output_dir=output_dir / "run2",
            output_format="flac",
            normalize_audio=False,
        )
        
        # Both should succeed independently
        assert result1.success is True
        assert result2.success is True
        
        # Results should be independent
        assert result1.metadata["normalized"] is True
        assert result2.metadata["normalized"] is False
