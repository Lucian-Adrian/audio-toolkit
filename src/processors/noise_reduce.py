"""Noise reduction processor using spectral subtraction."""

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
    from numpy.fft import fft, ifft
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False


class NoiseReducer(AudioProcessor):
    """
    Noise reduction processor using spectral subtraction.
    
    Implements a simple but effective spectral subtraction algorithm
    that estimates noise from the beginning of the audio and subtracts
    it from the entire signal.
    """
    
    @property
    def name(self) -> str:
        return "noise_reduce"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Reduce background noise using spectral subtraction"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.VOICE
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec(
                name="noise_reduce_db",
                type="float",
                description="Amount of noise reduction in dB",
                required=False,
                default=12.0,
                min_value=0.0,
                max_value=40.0,
            ),
            ParameterSpec(
                name="noise_floor_ms",
                type="integer",
                description="Duration of noise floor estimation from start (ms)",
                required=False,
                default=500,
                min_value=100,
                max_value=5000,
            ),
            ParameterSpec(
                name="smoothing_factor",
                type="float",
                description="Smoothing factor for noise estimation (0.0-1.0)",
                required=False,
                default=0.5,
                min_value=0.0,
                max_value=1.0,
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
    
    def _estimate_noise_profile(
        self,
        samples: "np.ndarray",
        noise_samples: int,
        window_size: int,
    ) -> "np.ndarray":
        """
        Estimate noise profile from beginning of audio.
        
        Args:
            samples: Audio samples (mono)
            noise_samples: Number of samples to use for noise estimation
            window_size: FFT window size
            
        Returns:
            Average noise magnitude spectrum
        """
        noise_section = samples[:noise_samples]
        
        # Use overlapping windows
        hop_size = window_size // 2
        num_windows = max(1, (len(noise_section) - window_size) // hop_size + 1)
        
        noise_spectrum = np.zeros(window_size)
        window = np.hanning(window_size)
        
        for i in range(num_windows):
            start = i * hop_size
            end = start + window_size
            if end > len(noise_section):
                break
            
            windowed = noise_section[start:end] * window
            spectrum = np.abs(fft(windowed))
            noise_spectrum += spectrum
        
        noise_spectrum /= num_windows
        return noise_spectrum
    
    def _spectral_subtraction(
        self,
        samples: "np.ndarray",
        noise_profile: "np.ndarray",
        reduction_factor: float,
        smoothing_factor: float,
    ) -> "np.ndarray":
        """
        Apply spectral subtraction noise reduction.
        
        Args:
            samples: Audio samples (mono)
            noise_profile: Estimated noise spectrum
            reduction_factor: How much to reduce noise
            smoothing_factor: Smoothing between frames
            
        Returns:
            Processed audio samples
        """
        window_size = len(noise_profile)
        hop_size = window_size // 2
        window = np.hanning(window_size)
        
        # Prepare output array
        output = np.zeros(len(samples))
        window_sum = np.zeros(len(samples))
        
        # Previous magnitude for smoothing
        prev_mag = None
        
        for i in range(0, len(samples) - window_size, hop_size):
            # Extract and window frame
            frame = samples[i:i + window_size] * window
            
            # FFT
            spectrum = fft(frame)
            magnitude = np.abs(spectrum)
            phase = np.angle(spectrum)
            
            # Subtract noise
            magnitude_reduced = magnitude - reduction_factor * noise_profile
            
            # Apply floor to avoid negative values and musical noise
            floor = 0.02 * noise_profile
            magnitude_reduced = np.maximum(magnitude_reduced, floor)
            
            # Smooth with previous frame to reduce artifacts
            if prev_mag is not None:
                magnitude_reduced = (
                    smoothing_factor * prev_mag +
                    (1 - smoothing_factor) * magnitude_reduced
                )
            prev_mag = magnitude_reduced.copy()
            
            # Reconstruct spectrum
            spectrum_reduced = magnitude_reduced * np.exp(1j * phase)
            
            # IFFT
            frame_reduced = np.real(ifft(spectrum_reduced))
            
            # Overlap-add
            output[i:i + window_size] += frame_reduced * window
            window_sum[i:i + window_size] += window ** 2
        
        # Normalize by window sum (avoid division by zero)
        window_sum = np.maximum(window_sum, 1e-8)
        output = output / window_sum
        
        return output
    
    def _process_channel(
        self,
        samples: "np.ndarray",
        noise_floor_samples: int,
        window_size: int,
        reduction_factor: float,
        smoothing_factor: float,
    ) -> "np.ndarray":
        """Process a single audio channel."""
        # Estimate noise profile
        noise_profile = self._estimate_noise_profile(
            samples, noise_floor_samples, window_size
        )
        
        # Apply spectral subtraction
        processed = self._spectral_subtraction(
            samples, noise_profile, reduction_factor, smoothing_factor
        )
        
        return processed
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        noise_reduce_db: float = 12.0,
        noise_floor_ms: int = 500,
        smoothing_factor: float = 0.5,
        output_format: str = "wav",
        **kwargs
    ) -> ProcessResult:
        """
        Apply noise reduction to audio file.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output file
            noise_reduce_db: Amount of noise reduction in dB
            noise_floor_ms: Duration of noise estimation in ms
            smoothing_factor: Smoothing between frames
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
            
            # Calculate parameters
            noise_floor_samples = int(audio.frame_rate * noise_floor_ms / 1000)
            window_size = 2048  # Good balance of frequency/time resolution
            reduction_factor = 10 ** (noise_reduce_db / 20)
            
            if noise_floor_samples >= len(samples):
                raise ValidationError(
                    f"Noise floor duration ({noise_floor_ms}ms) is too long for audio"
                )
            
            logger.info(
                f"Processing with {noise_reduce_db}dB reduction, "
                f"{noise_floor_ms}ms noise floor"
            )
            
            # Process each channel
            processed_channels = []
            for ch in range(samples.shape[1]):
                logger.debug(f"Processing channel {ch + 1}")
                processed = self._process_channel(
                    samples[:, ch],
                    noise_floor_samples,
                    window_size,
                    reduction_factor,
                    smoothing_factor,
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
            output_path = output_dir / f"{input_path.stem}_denoised.{output_format}"
            logger.info(f"Exporting to: {output_path}")
            
            processed_audio.export(output_path, format=output_format)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return ProcessResult(
                success=True,
                input_path=input_path,
                output_paths=[output_path],
                metadata={
                    "noise_reduce_db": noise_reduce_db,
                    "noise_floor_ms": noise_floor_ms,
                    "smoothing_factor": smoothing_factor,
                    "output_format": output_format,
                    "channels_processed": audio.channels,
                },
                processing_time_ms=elapsed_ms,
            )
            
        except (ValidationError, ProcessingError) as e:
            logger.error(f"Noise reduction failed: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.exception(f"Unexpected error during noise reduction: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=f"Unexpected error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )
