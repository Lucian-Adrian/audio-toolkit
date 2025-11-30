"""Audio visualizer for generating spectrograms and waveforms."""

import json
import time
from pathlib import Path
from typing import List, Optional

from ..core.exceptions import ProcessingError, ValidationError
from ..core.interfaces import AudioProcessor
from ..core.types import ParameterSpec, ProcessorCategory, ProcessResult
from ..utils.file_ops import ensure_directory
from ..utils.logger import get_logger
from ..utils.validators import validate_input_file

logger = get_logger(__name__)

# Optional imports - these are not required for basic functionality
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False


class AudioVisualizer(AudioProcessor):
    """
    Audio visualizer for generating spectrograms and waveforms.
    
    Generates PNG images showing:
    - Mel spectrograms
    - Waveform plots
    - Combined visualizations
    """
    
    @property
    def name(self) -> str:
        return "visualizer"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Generate spectrograms and waveform visualizations"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.ANALYSIS
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec(
                name="viz_type",
                type="string",
                description="Visualization type",
                required=False,
                default="waveform",
                choices=["waveform", "spectrogram", "mel", "combined"],
            ),
            ParameterSpec(
                name="width",
                type="integer",
                description="Image width in pixels",
                required=False,
                default=1200,
                min_value=400,
                max_value=4000,
            ),
            ParameterSpec(
                name="height",
                type="integer",
                description="Image height in pixels",
                required=False,
                default=400,
                min_value=200,
                max_value=2000,
            ),
            ParameterSpec(
                name="dpi",
                type="integer",
                description="Image DPI (dots per inch)",
                required=False,
                default=100,
                min_value=50,
                max_value=300,
            ),
            ParameterSpec(
                name="colormap",
                type="string",
                description="Colormap for spectrograms",
                required=False,
                default="viridis",
                choices=["viridis", "plasma", "inferno", "magma", "cividis", "hot", "cool"],
            ),
        ]
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are available."""
        missing = []
        if not HAS_NUMPY:
            missing.append("numpy")
        if not HAS_MATPLOTLIB:
            missing.append("matplotlib")
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
        
        # Handle stereo by taking mean
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
            samples = samples.mean(axis=1)
        
        # Normalize to -1.0 to 1.0
        max_val = float(2 ** (audio.sample_width * 8 - 1))
        samples = samples.astype(np.float64) / max_val
        
        return samples
    
    def _generate_waveform(
        self,
        samples: "np.ndarray",
        sample_rate: int,
        output_path: Path,
        width: int,
        height: int,
        dpi: int,
    ) -> None:
        """Generate waveform visualization."""
        duration = len(samples) / sample_rate
        time_axis = np.linspace(0, duration, len(samples))
        
        fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
        
        # Downsample for performance if needed
        if len(samples) > 10000:
            step = len(samples) // 10000
            samples = samples[::step]
            time_axis = time_axis[::step]
        
        ax.plot(time_axis, samples, color='#2196F3', linewidth=0.5)
        ax.fill_between(time_axis, samples, alpha=0.3, color='#2196F3')
        
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Amplitude')
        ax.set_title('Audio Waveform')
        ax.set_xlim(0, duration)
        ax.set_ylim(-1.1, 1.1)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    
    def _generate_spectrogram(
        self,
        samples: "np.ndarray",
        sample_rate: int,
        output_path: Path,
        width: int,
        height: int,
        dpi: int,
        colormap: str,
        mel: bool = False,
    ) -> None:
        """Generate spectrogram visualization."""
        fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
        
        # Use matplotlib's specgram which doesn't require scipy
        nfft = min(2048, len(samples))
        noverlap = nfft // 2
        
        if mel:
            # Simplified mel-scale approximation using log frequency scaling
            spec, freqs, times, im = ax.specgram(
                samples,
                Fs=sample_rate,
                NFFT=nfft,
                noverlap=noverlap,
                cmap=colormap,
                scale='dB',
            )
            ax.set_yscale('symlog', linthresh=1000)
            ax.set_title('Mel Spectrogram (Approximated)')
        else:
            spec, freqs, times, im = ax.specgram(
                samples,
                Fs=sample_rate,
                NFFT=nfft,
                noverlap=noverlap,
                cmap=colormap,
                scale='dB',
            )
            ax.set_title('Spectrogram')
        
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Frequency (Hz)')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Intensity (dB)')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    
    def _generate_combined(
        self,
        samples: "np.ndarray",
        sample_rate: int,
        output_path: Path,
        width: int,
        height: int,
        dpi: int,
        colormap: str,
    ) -> None:
        """Generate combined waveform and spectrogram visualization."""
        duration = len(samples) / sample_rate
        time_axis = np.linspace(0, duration, len(samples))
        
        fig, (ax1, ax2) = plt.subplots(
            2, 1,
            figsize=(width / dpi, height / dpi),
            dpi=dpi,
            height_ratios=[1, 2]
        )
        
        # Waveform
        plot_samples = samples
        plot_time = time_axis
        if len(samples) > 10000:
            step = len(samples) // 10000
            plot_samples = samples[::step]
            plot_time = time_axis[::step]
        
        ax1.plot(plot_time, plot_samples, color='#2196F3', linewidth=0.5)
        ax1.fill_between(plot_time, plot_samples, alpha=0.3, color='#2196F3')
        ax1.set_ylabel('Amplitude')
        ax1.set_xlim(0, duration)
        ax1.set_ylim(-1.1, 1.1)
        ax1.grid(True, alpha=0.3)
        ax1.set_title('Audio Waveform & Spectrogram')
        
        # Spectrogram
        nfft = min(2048, len(samples))
        noverlap = nfft // 2
        spec, freqs, times, im = ax2.specgram(
            samples,
            Fs=sample_rate,
            NFFT=nfft,
            noverlap=noverlap,
            cmap=colormap,
            scale='dB',
        )
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel('Frequency (Hz)')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        viz_type: str = "waveform",
        width: int = 1200,
        height: int = 400,
        dpi: int = 100,
        colormap: str = "viridis",
        **kwargs
    ) -> ProcessResult:
        """
        Generate audio visualization.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output image
            viz_type: Type of visualization
            width: Image width in pixels
            height: Image height in pixels
            dpi: Image DPI
            colormap: Colormap for spectrograms
            
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
            
            # Generate output path
            suffix = f"_{viz_type}" if viz_type != "waveform" else ""
            output_path = output_dir / f"{input_path.stem}{suffix}.png"
            
            # Generate visualization
            logger.info(f"Generating {viz_type} visualization")
            
            if viz_type == "waveform":
                self._generate_waveform(samples, sample_rate, output_path, width, height, dpi)
            elif viz_type == "spectrogram":
                self._generate_spectrogram(samples, sample_rate, output_path, width, height, dpi, colormap, mel=False)
            elif viz_type == "mel":
                self._generate_spectrogram(samples, sample_rate, output_path, width, height, dpi, colormap, mel=True)
            elif viz_type == "combined":
                height = max(height, 600)  # Ensure enough height for combined view
                self._generate_combined(samples, sample_rate, output_path, width, height, dpi, colormap)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Visualization complete: {output_path}")
            
            return ProcessResult(
                success=True,
                input_path=input_path,
                output_paths=[output_path],
                metadata={
                    "viz_type": viz_type,
                    "width": width,
                    "height": height,
                    "dpi": dpi,
                    "duration_seconds": len(audio) / 1000,
                    "sample_rate": sample_rate,
                    "processor": self.name,
                    "version": self.version,
                },
                processing_time_ms=elapsed_ms,
            )
            
        except (ValidationError, ProcessingError) as e:
            logger.error(f"Visualization failed: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.exception(f"Unexpected error during visualization: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=f"Unexpected error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )
