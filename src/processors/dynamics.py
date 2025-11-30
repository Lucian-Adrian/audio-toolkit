"""Dynamics processor for compression and EQ."""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.exceptions import ProcessingError, ValidationError
from ..core.interfaces import AudioProcessor
from ..core.types import ParameterSpec, ProcessorCategory, ProcessResult
from ..utils.file_ops import ensure_directory
from ..utils.logger import get_logger
from ..utils.validators import validate_input_file

logger = get_logger(__name__)

# Optional numpy import
try:
    import numpy as np
    from numpy.fft import fft, ifft, rfft, irfft
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False


class DynamicsProcessor(AudioProcessor):
    """
    Dynamics processor for compression and 3-band EQ.
    
    Features:
    - Compressor with threshold, ratio, attack/release
    - 3-band EQ (low, mid, high)
    - Output gain control
    """
    
    @property
    def name(self) -> str:
        return "dynamics"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Apply dynamics processing (compression, 3-band EQ)"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.VOICE
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return [
            # Compressor params
            ParameterSpec(
                name="compressor_threshold",
                type="float",
                description="Compressor threshold in dBFS",
                required=False,
                default=-20.0,
                min_value=-60.0,
                max_value=0.0,
            ),
            ParameterSpec(
                name="compressor_ratio",
                type="float",
                description="Compression ratio (e.g., 4.0 = 4:1)",
                required=False,
                default=4.0,
                min_value=1.0,
                max_value=20.0,
            ),
            ParameterSpec(
                name="compressor_attack_ms",
                type="float",
                description="Compressor attack time in milliseconds",
                required=False,
                default=10.0,
                min_value=0.1,
                max_value=500.0,
            ),
            ParameterSpec(
                name="compressor_release_ms",
                type="float",
                description="Compressor release time in milliseconds",
                required=False,
                default=100.0,
                min_value=10.0,
                max_value=2000.0,
            ),
            # EQ params
            ParameterSpec(
                name="eq_low_gain",
                type="float",
                description="Low frequency gain in dB (cutoff ~200Hz)",
                required=False,
                default=0.0,
                min_value=-12.0,
                max_value=12.0,
            ),
            ParameterSpec(
                name="eq_mid_gain",
                type="float",
                description="Mid frequency gain in dB (200Hz-4kHz)",
                required=False,
                default=0.0,
                min_value=-12.0,
                max_value=12.0,
            ),
            ParameterSpec(
                name="eq_high_gain",
                type="float",
                description="High frequency gain in dB (above 4kHz)",
                required=False,
                default=0.0,
                min_value=-12.0,
                max_value=12.0,
            ),
            # Output
            ParameterSpec(
                name="output_gain",
                type="float",
                description="Output gain in dB",
                required=False,
                default=0.0,
                min_value=-20.0,
                max_value=20.0,
            ),
            ParameterSpec(
                name="output_format",
                type="string",
                description="Output audio format",
                required=False,
                default="wav",
                choices=["wav", "mp3", "ogg", "flac"],
            ),
        ]
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are available."""
        missing = []
        if not HAS_NUMPY:
            missing.append("numpy")
        if not HAS_PYDUB:
            missing.append("pydub")
        
        if missing:
            raise ProcessingError(
                f"Missing required dependencies: {', '.join(missing)}. "
                f"Install with: pip install {' '.join(missing)}"
            )
    
    def _audio_to_samples(self, audio: "AudioSegment") -> "np.ndarray":
        """Convert AudioSegment to numpy array of samples."""
        samples = np.array(audio.get_array_of_samples())
        
        # Normalize to -1.0 to 1.0
        max_val = float(2 ** (audio.sample_width * 8 - 1))
        samples = samples.astype(np.float64) / max_val
        
        # Handle stereo by reshaping
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
        else:
            samples = samples.reshape((-1, 1))
        
        return samples
    
    def _samples_to_audio(
        self,
        samples: "np.ndarray",
        sample_rate: int,
        sample_width: int,
        channels: int,
    ) -> "AudioSegment":
        """Convert numpy samples back to AudioSegment."""
        # Flatten if stereo
        if channels == 2:
            samples = samples.flatten()
        else:
            samples = samples.ravel()
        
        # Convert back to integer range
        max_val = float(2 ** (sample_width * 8 - 1))
        samples = np.clip(samples * max_val, -max_val, max_val - 1)
        samples = samples.astype(np.int16)
        
        # Create AudioSegment
        audio = AudioSegment(
            samples.tobytes(),
            frame_rate=sample_rate,
            sample_width=sample_width,
            channels=channels,
        )
        
        return audio
    
    def _apply_compression(
        self,
        samples: "np.ndarray",
        threshold_db: float,
        ratio: float,
        attack_samples: int,
        release_samples: int,
    ) -> "np.ndarray":
        """
        Apply dynamic range compression.
        
        Args:
            samples: Audio samples
            threshold_db: Threshold in dBFS
            ratio: Compression ratio
            attack_samples: Attack time in samples
            release_samples: Release time in samples
            
        Returns:
            Compressed audio samples
        """
        # Convert threshold to linear
        threshold = 10 ** (threshold_db / 20)
        
        # Calculate envelope
        envelope = np.abs(samples)
        
        # Smooth envelope with attack/release
        smoothed_envelope = np.zeros_like(envelope)
        attack_coef = 1 - np.exp(-1 / attack_samples)
        release_coef = 1 - np.exp(-1 / release_samples)
        
        prev_env = 0
        for i in range(len(envelope)):
            if envelope[i] > prev_env:
                # Attack
                smoothed_envelope[i] = attack_coef * envelope[i] + (1 - attack_coef) * prev_env
            else:
                # Release
                smoothed_envelope[i] = release_coef * envelope[i] + (1 - release_coef) * prev_env
            prev_env = smoothed_envelope[i]
        
        # Calculate gain reduction
        gain = np.ones_like(samples)
        above_threshold = smoothed_envelope > threshold
        
        if np.any(above_threshold):
            # Calculate gain reduction for samples above threshold
            over_db = 20 * np.log10(smoothed_envelope[above_threshold] / threshold + 1e-10)
            reduced_db = over_db / ratio
            gain[above_threshold] = threshold * (10 ** (reduced_db / 20)) / (smoothed_envelope[above_threshold] + 1e-10)
        
        return samples * gain
    
    def _design_bandpass_filter(
        self,
        n_fft: int,
        sample_rate: int,
        low_freq: float,
        high_freq: float,
    ) -> "np.ndarray":
        """Design a simple bandpass filter in frequency domain."""
        freqs = np.fft.rfftfreq(n_fft, 1 / sample_rate)
        
        # Create smooth transitions
        filter_response = np.zeros(len(freqs))
        
        # Transition width (in Hz)
        transition = min(50, (high_freq - low_freq) / 4)
        
        for i, f in enumerate(freqs):
            if f < low_freq - transition:
                filter_response[i] = 0
            elif f < low_freq + transition:
                # Smooth transition in
                filter_response[i] = 0.5 * (1 + np.cos(np.pi * (low_freq - f) / transition))
            elif f < high_freq - transition:
                filter_response[i] = 1
            elif f < high_freq + transition:
                # Smooth transition out
                filter_response[i] = 0.5 * (1 + np.cos(np.pi * (f - high_freq) / transition))
            else:
                filter_response[i] = 0
        
        return filter_response
    
    def _apply_eq(
        self,
        samples: "np.ndarray",
        sample_rate: int,
        low_gain_db: float,
        mid_gain_db: float,
        high_gain_db: float,
    ) -> "np.ndarray":
        """
        Apply 3-band EQ using FFT filtering.
        
        Bands:
        - Low: 0-200 Hz
        - Mid: 200-4000 Hz
        - High: 4000+ Hz
        """
        low_cutoff = 200
        high_cutoff = 4000
        
        # Convert gains to linear
        low_gain = 10 ** (low_gain_db / 20)
        mid_gain = 10 ** (mid_gain_db / 20)
        high_gain = 10 ** (high_gain_db / 20)
        
        # Use FFT
        n_fft = len(samples)
        spectrum = rfft(samples)
        
        # Design band filters
        low_filter = self._design_bandpass_filter(n_fft, sample_rate, 0, low_cutoff)
        mid_filter = self._design_bandpass_filter(n_fft, sample_rate, low_cutoff, high_cutoff)
        high_filter = self._design_bandpass_filter(n_fft, sample_rate, high_cutoff, sample_rate / 2)
        
        # Apply gains
        eq_response = (
            low_gain * low_filter +
            mid_gain * mid_filter +
            high_gain * high_filter
        )
        
        # Apply EQ
        spectrum_eq = spectrum * eq_response
        
        return irfft(spectrum_eq, n=n_fft)
    
    def _apply_gain(self, samples: "np.ndarray", gain_db: float) -> "np.ndarray":
        """Apply output gain."""
        gain = 10 ** (gain_db / 20)
        return samples * gain
    
    def _process_channel(
        self,
        samples: "np.ndarray",
        sample_rate: int,
        compressor_threshold: float,
        compressor_ratio: float,
        attack_samples: int,
        release_samples: int,
        eq_low_gain: float,
        eq_mid_gain: float,
        eq_high_gain: float,
        output_gain: float,
    ) -> "np.ndarray":
        """Process a single audio channel."""
        processed = samples.copy()
        
        # Apply compression
        if compressor_ratio > 1.0:
            processed = self._apply_compression(
                processed,
                compressor_threshold,
                compressor_ratio,
                attack_samples,
                release_samples,
            )
        
        # Apply EQ
        if any(g != 0 for g in [eq_low_gain, eq_mid_gain, eq_high_gain]):
            processed = self._apply_eq(
                processed,
                sample_rate,
                eq_low_gain,
                eq_mid_gain,
                eq_high_gain,
            )
        
        # Apply output gain
        if output_gain != 0:
            processed = self._apply_gain(processed, output_gain)
        
        # Clip to prevent clipping
        processed = np.clip(processed, -1.0, 1.0)
        
        return processed
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        compressor_threshold: float = -20.0,
        compressor_ratio: float = 4.0,
        compressor_attack_ms: float = 10.0,
        compressor_release_ms: float = 100.0,
        eq_low_gain: float = 0.0,
        eq_mid_gain: float = 0.0,
        eq_high_gain: float = 0.0,
        output_gain: float = 0.0,
        output_format: str = "wav",
        **kwargs
    ) -> ProcessResult:
        """
        Apply dynamics processing to audio file.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output file
            compressor_threshold: Threshold in dBFS
            compressor_ratio: Compression ratio
            compressor_attack_ms: Attack time in ms
            compressor_release_ms: Release time in ms
            eq_low_gain: Low band gain in dB
            eq_mid_gain: Mid band gain in dB
            eq_high_gain: High band gain in dB
            output_gain: Output gain in dB
            output_format: Output audio format
            
        Returns:
            ProcessResult with success status and output path
        """
        start_time = time.time()
        
        try:
            # Check dependencies
            self._check_dependencies()
            
            # Validate inputs
            validate_input_file(input_path)
            ensure_directory(output_dir)
            
            # Load audio
            logger.info(f"Loading audio: {input_path}")
            audio = AudioSegment.from_file(input_path)
            
            samples = self._audio_to_samples(audio)
            sample_rate = audio.frame_rate
            
            # Calculate time constants in samples
            attack_samples = max(1, int(sample_rate * compressor_attack_ms / 1000))
            release_samples = max(1, int(sample_rate * compressor_release_ms / 1000))
            
            logger.info(
                f"Processing: threshold={compressor_threshold}dB, "
                f"ratio={compressor_ratio}:1, "
                f"EQ=[{eq_low_gain}, {eq_mid_gain}, {eq_high_gain}]dB"
            )
            
            # Process each channel
            processed_channels = []
            for ch in range(samples.shape[1]):
                logger.debug(f"Processing channel {ch + 1}")
                processed = self._process_channel(
                    samples[:, ch],
                    sample_rate,
                    compressor_threshold,
                    compressor_ratio,
                    attack_samples,
                    release_samples,
                    eq_low_gain,
                    eq_mid_gain,
                    eq_high_gain,
                    output_gain,
                )
                processed_channels.append(processed)
            
            # Combine channels
            processed_samples = np.column_stack(processed_channels)
            
            # Convert back to audio
            processed_audio = self._samples_to_audio(
                processed_samples,
                audio.frame_rate,
                audio.sample_width,
                audio.channels,
            )
            
            # Export
            output_path = output_dir / f"{input_path.stem}_processed.{output_format}"
            logger.info(f"Exporting to: {output_path}")
            
            processed_audio.export(output_path, format=output_format)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return ProcessResult(
                success=True,
                input_path=input_path,
                output_paths=[output_path],
                metadata={
                    "compressor": {
                        "threshold_db": compressor_threshold,
                        "ratio": compressor_ratio,
                        "attack_ms": compressor_attack_ms,
                        "release_ms": compressor_release_ms,
                    },
                    "eq": {
                        "low_gain_db": eq_low_gain,
                        "mid_gain_db": eq_mid_gain,
                        "high_gain_db": eq_high_gain,
                    },
                    "output_gain_db": output_gain,
                    "output_format": output_format,
                },
                processing_time_ms=elapsed_ms,
            )
            
        except (ValidationError, ProcessingError) as e:
            logger.error(f"Dynamics processing failed: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.exception(f"Unexpected error during dynamics processing: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=f"Unexpected error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )
