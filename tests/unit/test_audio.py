"""Unit tests for audio utilities."""

import pytest
from pathlib import Path

from pydub import AudioSegment
from pydub.generators import Sine

from src.utils.audio import (
    load_audio,
    get_audio_info,
    export_audio,
    get_duration_ms,
    split_audio,
    calculate_segments,
)
from src.core.exceptions import CorruptedFileError, UnsupportedFormatError


class TestLoadAudio:
    """Tests for load_audio function."""
    
    def test_load_audio_success(self, sample_audio_5sec):
        """Test loading a valid audio file."""
        audio = load_audio(sample_audio_5sec)
        
        assert isinstance(audio, AudioSegment)
        assert len(audio) > 0
    
    def test_load_audio_unsupported_format(self, temp_dir):
        """Test loading unsupported format raises error."""
        unsupported = temp_dir / "test.xyz"
        unsupported.write_text("not audio")
        
        with pytest.raises(UnsupportedFormatError):
            load_audio(unsupported)
    
    def test_load_audio_corrupted_file(self, temp_dir):
        """Test loading corrupted file raises error."""
        corrupted = temp_dir / "corrupted.wav"
        corrupted.write_text("not a real wav file")
        
        with pytest.raises(CorruptedFileError):
            load_audio(corrupted)


class TestGetAudioInfo:
    """Tests for get_audio_info function."""
    
    def test_get_audio_info_success(self, sample_audio_5sec):
        """Test getting audio file information."""
        info = get_audio_info(sample_audio_5sec)
        
        assert info.path == sample_audio_5sec
        assert info.format == "wav"
        assert info.duration_ms > 0
        assert info.sample_rate > 0
        assert info.channels >= 1
    
    def test_get_audio_info_unsupported(self, temp_dir):
        """Test getting info for unsupported format."""
        unsupported = temp_dir / "test.xyz"
        unsupported.write_text("not audio")
        
        with pytest.raises(UnsupportedFormatError):
            get_audio_info(unsupported)


class TestExportAudio:
    """Tests for export_audio function."""
    
    def test_export_audio_mp3(self, temp_dir):
        """Test exporting to MP3."""
        audio = Sine(440).to_audio_segment(duration=1000)
        output_path = temp_dir / "output.mp3"
        
        result = export_audio(audio, output_path, format="mp3", bitrate="192k")
        
        assert result == output_path
        assert output_path.exists()
    
    def test_export_audio_wav(self, temp_dir):
        """Test exporting to WAV."""
        audio = Sine(440).to_audio_segment(duration=1000)
        output_path = temp_dir / "output.wav"
        
        result = export_audio(audio, output_path, format="wav")
        
        assert result == output_path
        assert output_path.exists()
    
    def test_export_audio_infer_format(self, temp_dir):
        """Test format inference from extension."""
        audio = Sine(440).to_audio_segment(duration=1000)
        output_path = temp_dir / "output.flac"
        
        result = export_audio(audio, output_path)  # No format specified
        
        assert result == output_path
        assert output_path.exists()
    
    def test_export_audio_creates_parent_dirs(self, temp_dir):
        """Test that parent directories are created."""
        audio = Sine(440).to_audio_segment(duration=1000)
        nested_dir = temp_dir / "nested" / "deep" / "dir"
        output_path = nested_dir / "output.wav"
        
        result = export_audio(audio, output_path)
        
        assert result == output_path
        assert nested_dir.exists()
        assert output_path.exists()


class TestGetDurationMs:
    """Tests for get_duration_ms function."""
    
    def test_get_duration_ms(self, sample_audio_5sec):
        """Test getting duration in milliseconds."""
        duration = get_duration_ms(sample_audio_5sec)
        
        # Should be approximately 5000ms
        assert 4500 <= duration <= 5500


class TestSplitAudio:
    """Tests for split_audio function."""
    
    def test_split_audio_middle(self):
        """Test extracting middle segment."""
        audio = Sine(440).to_audio_segment(duration=5000)
        
        segment = split_audio(audio, 1000, 3000)
        
        assert len(segment) == 2000
    
    def test_split_audio_from_start(self):
        """Test extracting from start."""
        audio = Sine(440).to_audio_segment(duration=5000)
        
        segment = split_audio(audio, 0, 2000)
        
        assert len(segment) == 2000
    
    def test_split_audio_to_end(self):
        """Test extracting to end."""
        audio = Sine(440).to_audio_segment(duration=5000)
        
        segment = split_audio(audio, 3000, 5000)
        
        assert len(segment) == 2000


class TestCalculateSegments:
    """Tests for calculate_segments function."""
    
    def test_calculate_segments_exact_division(self):
        """Test with duration that divides evenly."""
        segments = calculate_segments(10000, 2000)
        
        assert len(segments) == 5
        assert segments[0] == (0, 2000)
        assert segments[-1] == (8000, 10000)
    
    def test_calculate_segments_with_remainder(self):
        """Test with remainder that's long enough."""
        segments = calculate_segments(10000, 3000, min_last_segment_ms=500)
        
        # 3 full segments (0-3000, 3000-6000, 6000-9000) + 1000 remainder
        assert len(segments) == 4
        assert segments[-1] == (9000, 10000)
    
    def test_calculate_segments_short_remainder_merged(self):
        """Test that short remainder is merged with previous."""
        segments = calculate_segments(10000, 3000, min_last_segment_ms=1500)
        
        # 3000+3000+3000+1000 = 10000
        # 1000 < 1500, so merged with previous
        assert len(segments) == 3
        assert segments[-1] == (6000, 10000)  # Extended segment
    
    def test_calculate_segments_single_segment(self):
        """Test when audio is shorter than segment duration."""
        segments = calculate_segments(1000, 5000)
        
        assert len(segments) == 1
        assert segments[0] == (0, 1000)
