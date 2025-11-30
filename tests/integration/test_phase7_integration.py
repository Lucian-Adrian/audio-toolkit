"""Integration tests for Phase 7 processors with real audio processing."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import struct

import pytest

from src.processors import (
    AudioVisualizer,
    AudioStatistics,
    NoiseReducer,
    DynamicsProcessor,
    AudioTrimmer,
    AudioTranscriber,
)


def create_test_wav(path: Path, duration_ms: int = 1000, frequency: int = 440) -> None:
    """Create a simple WAV file with a sine wave for testing."""
    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000)
    
    # Generate simple audio data (silence with some peaks)
    import math
    samples = []
    for i in range(num_samples):
        # Simple sine wave
        value = int(32767 * 0.5 * math.sin(2 * math.pi * frequency * i / sample_rate))
        samples.append(value)
    
    # Write WAV file
    with open(path, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        data_size = num_samples * 2  # 16-bit samples
        f.write(struct.pack('<I', 36 + data_size))  # File size - 8
        f.write(b'WAVE')
        
        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # Chunk size
        f.write(struct.pack('<H', 1))   # Audio format (PCM)
        f.write(struct.pack('<H', 1))   # Channels (mono)
        f.write(struct.pack('<I', sample_rate))  # Sample rate
        f.write(struct.pack('<I', sample_rate * 2))  # Byte rate
        f.write(struct.pack('<H', 2))   # Block align
        f.write(struct.pack('<H', 16))  # Bits per sample
        
        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        for sample in samples:
            f.write(struct.pack('<h', sample))


class TestAudioVisualizerIntegration:
    """Integration tests for AudioVisualizer with real audio files."""
    
    def test_visualizer_waveform(self, tmp_path):
        """Test waveform visualization with real audio."""
        # Create test audio
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file)
        
        processor = AudioVisualizer()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            viz_type="waveform",
        )
        
        assert result.success
        assert len(result.output_paths) == 1
        assert result.output_paths[0].exists()
        assert result.output_paths[0].suffix == ".png"
    
    def test_visualizer_spectrogram(self, tmp_path):
        """Test spectrogram visualization."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file)
        
        processor = AudioVisualizer()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            viz_type="spectrogram",
        )
        
        assert result.success
        assert result.output_paths[0].exists()
    
    def test_visualizer_combined(self, tmp_path):
        """Test combined visualization."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file)
        
        processor = AudioVisualizer()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            viz_type="combined",
        )
        
        assert result.success
    
    def test_visualizer_invalid_file(self, tmp_path):
        """Test visualizer with non-existent file."""
        processor = AudioVisualizer()
        result = processor.process(
            input_path=tmp_path / "nonexistent.wav",
            output_dir=tmp_path,
        )
        
        assert not result.success
        assert result.error_message is not None


class TestAudioStatisticsIntegration:
    """Integration tests for AudioStatistics with real audio files."""
    
    def test_statistics_json_output(self, tmp_path):
        """Test statistics with JSON output."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file, duration_ms=2000)
        
        processor = AudioStatistics()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            output_format="json",
        )
        
        assert result.success
        assert result.output_paths[0].suffix == ".json"
        assert result.metadata is not None
        assert "levels" in result.metadata
        assert "rms_db" in result.metadata["levels"]
    
    def test_statistics_txt_output(self, tmp_path):
        """Test statistics with text output."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file)
        
        processor = AudioStatistics()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            output_format="txt",
        )
        
        assert result.success
        assert result.output_paths[0].suffix == ".txt"
        
        # Check content
        content = result.output_paths[0].read_text()
        assert "RMS Level" in content
        assert "Peak Level" in content
    
    def test_statistics_metadata_structure(self, tmp_path):
        """Test that statistics metadata has expected structure."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file)
        
        processor = AudioStatistics()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
        )
        
        assert result.success
        metadata = result.metadata
        
        # Check file info
        assert "file" in metadata
        assert metadata["file"]["sample_rate"] == 44100
        assert metadata["file"]["channels"] == 1
        
        # Check levels
        assert "levels" in metadata
        assert "rms" in metadata["levels"]
        assert "peak" in metadata["levels"]
        
        # Check silence
        assert "silence" in metadata
        assert "ratio" in metadata["silence"]
        
        # Check VAD
        assert "vad" in metadata
        assert "voice_ratio" in metadata["vad"]


class TestNoiseReducerIntegration:
    """Integration tests for NoiseReducer."""
    
    def test_noise_reduce_basic(self, tmp_path):
        """Test basic noise reduction."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file, duration_ms=2000)
        
        processor = NoiseReducer()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            noise_reduce_db=10.0,
            noise_floor_ms=500,
        )
        
        assert result.success
        assert result.output_paths[0].exists()
        assert "_denoised" in result.output_paths[0].name
    
    def test_noise_reduce_with_smoothing(self, tmp_path):
        """Test noise reduction with high smoothing."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file, duration_ms=2000)
        
        processor = NoiseReducer()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            noise_reduce_db=15.0,
            smoothing_factor=0.8,
        )
        
        assert result.success
    
    def test_noise_reduce_too_long_noise_floor(self, tmp_path):
        """Test error when noise floor is too long."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file, duration_ms=500)  # Short audio
        
        processor = NoiseReducer()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            noise_floor_ms=1000,  # Longer than audio
        )
        
        assert not result.success
        assert "too long" in result.error_message.lower()


class TestDynamicsProcessorIntegration:
    """Integration tests for DynamicsProcessor."""
    
    def test_dynamics_compression(self, tmp_path):
        """Test dynamics processing with compression."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file)
        
        processor = DynamicsProcessor()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            compressor_threshold=-20.0,
            compressor_ratio=4.0,
        )
        
        assert result.success
        assert result.output_paths[0].exists()
    
    def test_dynamics_eq(self, tmp_path):
        """Test dynamics processing with EQ."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file)
        
        processor = DynamicsProcessor()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            eq_low_gain=-3.0,
            eq_mid_gain=2.0,
            eq_high_gain=1.0,
        )
        
        assert result.success
    
    def test_dynamics_full_chain(self, tmp_path):
        """Test dynamics with compression, EQ, and gain."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file)
        
        processor = DynamicsProcessor()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            compressor_threshold=-18.0,
            compressor_ratio=6.0,
            eq_low_gain=-2.0,
            eq_mid_gain=1.0,
            eq_high_gain=0.5,
            output_gain=3.0,
        )
        
        assert result.success
        assert result.metadata["compressor"]["ratio"] == 6.0


class TestAudioTrimmerIntegration:
    """Integration tests for AudioTrimmer."""
    
    def test_trim_edges(self, tmp_path):
        """Test trimming edges only."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file, duration_ms=2000)
        
        processor = AudioTrimmer()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            mode="edges",
            silence_threshold=-50.0,
        )
        
        assert result.success
        assert result.output_paths[0].exists()
    
    def test_trim_all(self, tmp_path):
        """Test trimming all silence."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file, duration_ms=2000)
        
        processor = AudioTrimmer()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            mode="all",
            silence_threshold=-50.0,
        )
        
        assert result.success
    
    def test_trim_with_padding(self, tmp_path):
        """Test trimming with padding."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file, duration_ms=2000)
        
        processor = AudioTrimmer()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
            padding_ms=100,
        )
        
        assert result.success


class TestAudioTranscriberIntegration:
    """Integration tests for AudioTranscriber."""
    
    @patch("src.processors.transcriber.HAS_WHISPER", False)
    def test_transcriber_missing_whisper(self, tmp_path):
        """Test error when whisper is not installed."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file)
        
        processor = AudioTranscriber()
        result = processor.process(
            input_path=audio_file,
            output_dir=tmp_path,
        )
        
        assert not result.success
        assert "whisper" in result.error_message.lower()
    
    def test_transcriber_format_methods(self):
        """Test transcriber output format methods."""
        processor = AudioTranscriber()
        
        # Test SRT timestamp formatting
        timestamp = processor._format_timestamp(3661.5)  # 1:01:01.500
        assert timestamp == "01:01:01,500"
        
        # Test VTT timestamp formatting
        vtt_timestamp = processor._format_vtt_timestamp(3661.5)
        assert vtt_timestamp == "01:01:01.500"
    
    def test_transcriber_format_txt(self):
        """Test text format output."""
        processor = AudioTranscriber()
        result = {"text": "  Hello World  "}
        
        formatted = processor._format_txt(result)
        assert formatted == "Hello World"
    
    def test_transcriber_format_srt(self):
        """Test SRT format output."""
        processor = AudioTranscriber()
        result = {
            "text": "Hello",
            "segments": [
                {"id": 0, "start": 0.0, "end": 1.0, "text": " Hello "},
                {"id": 1, "start": 1.5, "end": 2.5, "text": " World "},
            ]
        }
        
        srt = processor._format_srt(result)
        assert "1\n00:00:00,000 --> 00:00:01,000" in srt
        assert "Hello" in srt
        assert "2\n00:00:01,500 --> 00:00:02,500" in srt
    
    def test_transcriber_format_vtt(self):
        """Test VTT format output."""
        processor = AudioTranscriber()
        result = {
            "text": "Hello",
            "segments": [
                {"id": 0, "start": 0.0, "end": 1.0, "text": " Hello "},
            ]
        }
        
        vtt = processor._format_vtt(result)
        assert "WEBVTT" in vtt
        assert "00:00:00.000 --> 00:00:01.000" in vtt


class TestProcessorChaining:
    """Test chaining multiple processors together."""
    
    def test_denoise_then_dynamics(self, tmp_path):
        """Test running noise reduction then dynamics processing."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file, duration_ms=2000)
        
        # Step 1: Denoise
        noise_reducer = NoiseReducer()
        result1 = noise_reducer.process(
            input_path=audio_file,
            output_dir=tmp_path,
            noise_reduce_db=10.0,
        )
        assert result1.success
        
        # Step 2: Dynamics
        dynamics = DynamicsProcessor()
        result2 = dynamics.process(
            input_path=result1.output_paths[0],
            output_dir=tmp_path,
            compressor_threshold=-18.0,
        )
        assert result2.success
    
    def test_dynamics_then_trim(self, tmp_path):
        """Test running dynamics then trimming."""
        audio_file = tmp_path / "test.wav"
        create_test_wav(audio_file, duration_ms=2000)
        
        # Step 1: Dynamics
        dynamics = DynamicsProcessor()
        result1 = dynamics.process(
            input_path=audio_file,
            output_dir=tmp_path,
        )
        assert result1.success
        
        # Step 2: Trim
        trimmer = AudioTrimmer()
        result2 = trimmer.process(
            input_path=result1.output_paths[0],
            output_dir=tmp_path,
            mode="edges",
        )
        assert result2.success
