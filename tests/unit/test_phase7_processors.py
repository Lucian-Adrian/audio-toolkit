"""Tests for Phase 7 advanced processors."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.processors import (
    AudioVisualizer,
    AudioStatistics,
    NoiseReducer,
    DynamicsProcessor,
    AudioTrimmer,
    AudioTranscriber,
    get_processor,
    list_processors,
)
from src.core.types import ProcessorCategory


class TestProcessorRegistry:
    """Test that all new processors are registered."""
    
    def test_new_processors_registered(self):
        """All Phase 7 processors should be registered."""
        processors = list_processors()
        assert "visualizer" in processors
        assert "statistics" in processors
        assert "noise_reduce" in processors
        assert "dynamics" in processors
        assert "trimmer" in processors
        assert "transcriber" in processors
    
    def test_get_visualizer(self):
        """Can get visualizer processor by name."""
        processor = get_processor("visualizer")
        assert isinstance(processor, AudioVisualizer)
    
    def test_get_statistics(self):
        """Can get statistics processor by name."""
        processor = get_processor("statistics")
        assert isinstance(processor, AudioStatistics)
    
    def test_get_noise_reducer(self):
        """Can get noise_reduce processor by name."""
        processor = get_processor("noise_reduce")
        assert isinstance(processor, NoiseReducer)
    
    def test_get_dynamics(self):
        """Can get dynamics processor by name."""
        processor = get_processor("dynamics")
        assert isinstance(processor, DynamicsProcessor)
    
    def test_get_trimmer(self):
        """Can get trimmer processor by name."""
        processor = get_processor("trimmer")
        assert isinstance(processor, AudioTrimmer)
    
    def test_get_transcriber(self):
        """Can get transcriber processor by name."""
        processor = get_processor("transcriber")
        assert isinstance(processor, AudioTranscriber)


class TestAudioVisualizer:
    """Tests for AudioVisualizer processor."""
    
    def test_properties(self):
        """Test processor properties."""
        processor = AudioVisualizer()
        assert processor.name == "visualizer"
        assert processor.version == "1.0.0"
        assert processor.category == ProcessorCategory.ANALYSIS
        assert "waveform" in processor.description.lower() or "spectrogram" in processor.description.lower()
    
    def test_parameters(self):
        """Test processor has required parameters."""
        processor = AudioVisualizer()
        param_names = [p.name for p in processor.parameters]
        assert "viz_type" in param_names
        assert "width" in param_names
        assert "height" in param_names
        assert "colormap" in param_names
    
    def test_visualization_type_choices(self):
        """Test visualization type parameter has correct choices."""
        processor = AudioVisualizer()
        viz_param = next(p for p in processor.parameters if p.name == "viz_type")
        assert "waveform" in viz_param.choices
        assert "spectrogram" in viz_param.choices
        assert "mel" in viz_param.choices
        assert "combined" in viz_param.choices
    
    @patch("src.processors.visualizer.HAS_NUMPY", False)
    def test_missing_numpy_dependency(self, tmp_path):
        """Test error when numpy is missing."""
        processor = AudioVisualizer()
        result = processor.process(
            input_path=Path("test.wav"),
            output_dir=tmp_path,
        )
        assert not result.success
        assert "numpy" in result.error_message.lower()


class TestAudioStatistics:
    """Tests for AudioStatistics processor."""
    
    def test_properties(self):
        """Test processor properties."""
        processor = AudioStatistics()
        assert processor.name == "statistics"
        assert processor.version == "1.0.0"
        assert processor.category == ProcessorCategory.ANALYSIS
    
    def test_parameters(self):
        """Test processor has required parameters."""
        processor = AudioStatistics()
        param_names = [p.name for p in processor.parameters]
        assert "silence_threshold" in param_names
        assert "vad_threshold" in param_names
        assert "chunk_size_ms" in param_names
        assert "output_format" in param_names
    
    def test_output_format_choices(self):
        """Test output format parameter has correct choices."""
        processor = AudioStatistics()
        fmt_param = next(p for p in processor.parameters if p.name == "output_format")
        assert "json" in fmt_param.choices
        assert "txt" in fmt_param.choices
    
    @patch("src.processors.statistics.HAS_NUMPY", False)
    def test_missing_numpy_dependency(self, tmp_path):
        """Test error when numpy is missing."""
        processor = AudioStatistics()
        result = processor.process(
            input_path=Path("test.wav"),
            output_dir=tmp_path,
        )
        assert not result.success
        assert "numpy" in result.error_message.lower()


class TestNoiseReducer:
    """Tests for NoiseReducer processor."""
    
    def test_properties(self):
        """Test processor properties."""
        processor = NoiseReducer()
        assert processor.name == "noise_reduce"
        assert processor.version == "1.0.0"
        assert processor.category == ProcessorCategory.VOICE
    
    def test_parameters(self):
        """Test processor has required parameters."""
        processor = NoiseReducer()
        param_names = [p.name for p in processor.parameters]
        assert "noise_reduce_db" in param_names
        assert "noise_floor_ms" in param_names
        assert "smoothing_factor" in param_names
        assert "output_format" in param_names
    
    def test_noise_reduce_range(self):
        """Test noise reduction parameter has correct range."""
        processor = NoiseReducer()
        param = next(p for p in processor.parameters if p.name == "noise_reduce_db")
        assert param.default == 12.0
        assert param.min_value == 0.0
        assert param.max_value == 40.0
    
    @patch("src.processors.noise_reduce.HAS_NUMPY", False)
    def test_missing_numpy_dependency(self, tmp_path):
        """Test error when numpy is missing."""
        processor = NoiseReducer()
        result = processor.process(
            input_path=Path("test.wav"),
            output_dir=tmp_path,
        )
        assert not result.success
        assert "numpy" in result.error_message.lower()


class TestDynamicsProcessor:
    """Tests for DynamicsProcessor."""
    
    def test_properties(self):
        """Test processor properties."""
        processor = DynamicsProcessor()
        assert processor.name == "dynamics"
        assert processor.version == "1.0.0"
        assert processor.category == ProcessorCategory.VOICE
    
    def test_parameters(self):
        """Test processor has required parameters."""
        processor = DynamicsProcessor()
        param_names = [p.name for p in processor.parameters]
        # Compressor params
        assert "compressor_threshold" in param_names
        assert "compressor_ratio" in param_names
        assert "compressor_attack_ms" in param_names
        assert "compressor_release_ms" in param_names
        # EQ params
        assert "eq_low_gain" in param_names
        assert "eq_mid_gain" in param_names
        assert "eq_high_gain" in param_names
        # Output
        assert "output_gain" in param_names
        assert "output_format" in param_names
    
    def test_compressor_ratio_range(self):
        """Test compressor ratio parameter has correct range."""
        processor = DynamicsProcessor()
        param = next(p for p in processor.parameters if p.name == "compressor_ratio")
        assert param.default == 4.0
        assert param.min_value == 1.0
        assert param.max_value == 20.0
    
    def test_eq_gain_range(self):
        """Test EQ gain parameters have correct range."""
        processor = DynamicsProcessor()
        for name in ["eq_low_gain", "eq_mid_gain", "eq_high_gain"]:
            param = next(p for p in processor.parameters if p.name == name)
            assert param.min_value == -12.0
            assert param.max_value == 12.0
    
    @patch("src.processors.dynamics.HAS_NUMPY", False)
    def test_missing_numpy_dependency(self, tmp_path):
        """Test error when numpy is missing."""
        processor = DynamicsProcessor()
        result = processor.process(
            input_path=Path("test.wav"),
            output_dir=tmp_path,
        )
        assert not result.success
        assert "numpy" in result.error_message.lower()


class TestAudioTrimmer:
    """Tests for AudioTrimmer processor."""
    
    def test_properties(self):
        """Test processor properties."""
        processor = AudioTrimmer()
        assert processor.name == "trimmer"
        assert processor.version == "1.0.0"
        assert processor.category == ProcessorCategory.VOICE
    
    def test_parameters(self):
        """Test processor has required parameters."""
        processor = AudioTrimmer()
        param_names = [p.name for p in processor.parameters]
        assert "mode" in param_names
        assert "silence_threshold" in param_names
        assert "min_silence_ms" in param_names
        assert "padding_ms" in param_names
        assert "max_silence_ms" in param_names
        assert "output_format" in param_names
    
    def test_mode_choices(self):
        """Test mode parameter has correct choices."""
        processor = AudioTrimmer()
        mode_param = next(p for p in processor.parameters if p.name == "mode")
        assert "edges" in mode_param.choices
        assert "all" in mode_param.choices
    
    @patch("src.processors.trimmer.HAS_PYDUB", False)
    def test_missing_pydub_dependency(self, tmp_path):
        """Test error when pydub is missing."""
        processor = AudioTrimmer()
        result = processor.process(
            input_path=Path("test.wav"),
            output_dir=tmp_path,
        )
        assert not result.success
        assert "pydub" in result.error_message.lower()


class TestAudioTranscriber:
    """Tests for AudioTranscriber processor."""
    
    def test_properties(self):
        """Test processor properties."""
        processor = AudioTranscriber()
        assert processor.name == "transcriber"
        assert processor.version == "1.0.0"
        assert processor.category == ProcessorCategory.ANALYSIS
    
    def test_parameters(self):
        """Test processor has required parameters."""
        processor = AudioTranscriber()
        param_names = [p.name for p in processor.parameters]
        assert "model" in param_names
        assert "language" in param_names
        assert "output_format" in param_names
        assert "word_timestamps" in param_names
        assert "task" in param_names
    
    def test_model_choices(self):
        """Test model parameter has correct choices."""
        processor = AudioTranscriber()
        model_param = next(p for p in processor.parameters if p.name == "model")
        assert "tiny" in model_param.choices
        assert "base" in model_param.choices
        assert "small" in model_param.choices
        assert "medium" in model_param.choices
        assert "large" in model_param.choices
    
    def test_output_format_choices(self):
        """Test output format parameter has correct choices."""
        processor = AudioTranscriber()
        fmt_param = next(p for p in processor.parameters if p.name == "output_format")
        assert "txt" in fmt_param.choices
        assert "json" in fmt_param.choices
        assert "srt" in fmt_param.choices
        assert "vtt" in fmt_param.choices
    
    def test_task_choices(self):
        """Test task parameter has correct choices."""
        processor = AudioTranscriber()
        task_param = next(p for p in processor.parameters if p.name == "task")
        assert "transcribe" in task_param.choices
        assert "translate" in task_param.choices
    
    @patch("src.processors.transcriber.HAS_WHISPER", False)
    def test_missing_whisper_dependency(self, tmp_path):
        """Test error when whisper is missing."""
        processor = AudioTranscriber()
        result = processor.process(
            input_path=Path("test.wav"),
            output_dir=tmp_path,
        )
        assert not result.success
        assert "whisper" in result.error_message.lower()
    
    def test_model_info(self):
        """Test MODEL_INFO class attribute."""
        assert "tiny" in AudioTranscriber.MODEL_INFO
        assert "base" in AudioTranscriber.MODEL_INFO
        assert "params" in AudioTranscriber.MODEL_INFO["base"]
        assert "vram" in AudioTranscriber.MODEL_INFO["base"]
