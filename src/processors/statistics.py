"""Audio statistics analyzer for extracting audio metrics."""

import json
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
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False


class AudioStatistics(AudioProcessor):
    """
    Audio statistics analyzer.
    
    Calculates:
    - RMS (Root Mean Square) level
    - Peak amplitude
    - Dynamic range
    - Silence ratio
    - Voice Activity Detection (VAD)
    - Duration and format info
    """
    
    @property
    def name(self) -> str:
        return "statistics"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Analyze audio and extract statistics (RMS, peak, silence ratio, VAD)"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.ANALYSIS
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec(
                name="silence_threshold",
                type="float",
                description="Silence threshold in dBFS",
                required=False,
                default=-40.0,
                min_value=-80.0,
                max_value=-10.0,
            ),
            ParameterSpec(
                name="vad_threshold",
                type="float",
                description="Voice activity threshold in dBFS",
                required=False,
                default=-30.0,
                min_value=-80.0,
                max_value=-10.0,
            ),
            ParameterSpec(
                name="chunk_size_ms",
                type="integer",
                description="Chunk size for analysis in milliseconds",
                required=False,
                default=100,
                min_value=10,
                max_value=1000,
            ),
            ParameterSpec(
                name="output_format",
                type="string",
                description="Output format for statistics",
                required=False,
                default="json",
                choices=["json", "txt"],
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
        
        # Handle stereo by taking mean
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
            samples = samples.mean(axis=1)
        
        # Normalize to -1.0 to 1.0
        max_val = float(2 ** (audio.sample_width * 8 - 1))
        samples = samples.astype(np.float64) / max_val
        
        return samples
    
    def _calculate_rms(self, samples: "np.ndarray") -> float:
        """Calculate RMS level."""
        return float(np.sqrt(np.mean(samples ** 2)))
    
    def _calculate_rms_db(self, rms: float) -> float:
        """Convert RMS to dB."""
        if rms <= 0:
            return -100.0
        return float(20 * np.log10(rms))
    
    def _calculate_peak(self, samples: "np.ndarray") -> float:
        """Calculate peak amplitude."""
        return float(np.max(np.abs(samples)))
    
    def _calculate_peak_db(self, peak: float) -> float:
        """Convert peak to dB."""
        if peak <= 0:
            return -100.0
        return float(20 * np.log10(peak))
    
    def _calculate_dynamic_range(self, samples: "np.ndarray", chunk_size: int) -> float:
        """Calculate dynamic range in dB."""
        # Split into chunks and calculate RMS for each
        num_chunks = len(samples) // chunk_size
        if num_chunks < 2:
            return 0.0
        
        rms_values = []
        for i in range(num_chunks):
            chunk = samples[i * chunk_size:(i + 1) * chunk_size]
            rms = self._calculate_rms(chunk)
            if rms > 0:
                rms_values.append(rms)
        
        if len(rms_values) < 2:
            return 0.0
        
        rms_values = np.array(rms_values)
        max_rms = np.percentile(rms_values, 95)  # Avoid outliers
        min_rms = np.percentile(rms_values, 5)
        
        if min_rms <= 0:
            return 60.0  # Max reasonable dynamic range
        
        return float(20 * np.log10(max_rms / min_rms))
    
    def _calculate_silence_ratio(
        self,
        audio: "AudioSegment",
        threshold_dbfs: float,
        chunk_size_ms: int,
    ) -> float:
        """Calculate ratio of silent chunks."""
        if len(audio) < chunk_size_ms:
            return 0.0 if audio.dBFS > threshold_dbfs else 1.0
        
        silent_chunks = 0
        total_chunks = 0
        
        for i in range(0, len(audio), chunk_size_ms):
            chunk = audio[i:i + chunk_size_ms]
            if len(chunk) >= chunk_size_ms // 2:  # At least half a chunk
                total_chunks += 1
                if chunk.dBFS < threshold_dbfs:
                    silent_chunks += 1
        
        if total_chunks == 0:
            return 0.0
        
        return silent_chunks / total_chunks
    
    def _calculate_vad(
        self,
        audio: "AudioSegment",
        threshold_dbfs: float,
        chunk_size_ms: int,
    ) -> Dict[str, Any]:
        """
        Perform Voice Activity Detection.
        
        Returns:
            Dict with VAD statistics
        """
        if len(audio) < chunk_size_ms:
            is_voice = audio.dBFS > threshold_dbfs
            return {
                "voice_ratio": 1.0 if is_voice else 0.0,
                "voice_segments": 1 if is_voice else 0,
                "avg_segment_duration_ms": len(audio) if is_voice else 0,
                "total_voice_duration_ms": len(audio) if is_voice else 0,
            }
        
        voice_chunks = []
        
        for i in range(0, len(audio), chunk_size_ms):
            chunk = audio[i:i + chunk_size_ms]
            if len(chunk) >= chunk_size_ms // 2:
                voice_chunks.append(chunk.dBFS > threshold_dbfs)
        
        if not voice_chunks:
            return {
                "voice_ratio": 0.0,
                "voice_segments": 0,
                "avg_segment_duration_ms": 0,
                "total_voice_duration_ms": 0,
            }
        
        # Count voice segments (consecutive voice chunks)
        voice_segments = 0
        in_voice = False
        segment_durations = []
        current_duration = 0
        
        for is_voice in voice_chunks:
            if is_voice:
                if not in_voice:
                    voice_segments += 1
                    in_voice = True
                current_duration += chunk_size_ms
            else:
                if in_voice:
                    segment_durations.append(current_duration)
                    current_duration = 0
                in_voice = False
        
        if in_voice:
            segment_durations.append(current_duration)
        
        voice_count = sum(voice_chunks)
        voice_ratio = voice_count / len(voice_chunks)
        total_voice_ms = sum(segment_durations)
        avg_duration = total_voice_ms / voice_segments if voice_segments > 0 else 0
        
        return {
            "voice_ratio": voice_ratio,
            "voice_segments": voice_segments,
            "avg_segment_duration_ms": avg_duration,
            "total_voice_duration_ms": total_voice_ms,
        }
    
    def _format_output(
        self,
        stats: Dict[str, Any],
        output_format: str,
    ) -> str:
        """Format statistics for output."""
        if output_format == "json":
            return json.dumps(stats, indent=2)
        
        # Text format
        lines = [
            "=" * 50,
            "AUDIO STATISTICS REPORT",
            "=" * 50,
            "",
            f"File: {stats['file']['name']}",
            f"Duration: {stats['file']['duration_seconds']:.2f} seconds",
            f"Format: {stats['file']['format']}",
            f"Sample Rate: {stats['file']['sample_rate']} Hz",
            f"Channels: {stats['file']['channels']}",
            "",
            "--- Levels ---",
            f"RMS Level: {stats['levels']['rms_db']:.1f} dBFS",
            f"Peak Level: {stats['levels']['peak_db']:.1f} dBFS",
            f"Dynamic Range: {stats['levels']['dynamic_range_db']:.1f} dB",
            "",
            "--- Silence Analysis ---",
            f"Silence Ratio: {stats['silence']['ratio'] * 100:.1f}%",
            f"Threshold: {stats['silence']['threshold_dbfs']:.1f} dBFS",
            "",
            "--- Voice Activity ---",
            f"Voice Ratio: {stats['vad']['voice_ratio'] * 100:.1f}%",
            f"Voice Segments: {stats['vad']['voice_segments']}",
            f"Avg Segment Duration: {stats['vad']['avg_segment_duration_ms']:.0f} ms",
            f"Total Voice Duration: {stats['vad']['total_voice_duration_ms']:.0f} ms",
            "",
            "=" * 50,
        ]
        return "\n".join(lines)
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        silence_threshold: float = -40.0,
        vad_threshold: float = -30.0,
        chunk_size_ms: int = 100,
        output_format: str = "json",
        **kwargs
    ) -> ProcessResult:
        """
        Analyze audio and generate statistics.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output file
            silence_threshold: Silence threshold in dBFS
            vad_threshold: Voice activity threshold in dBFS
            chunk_size_ms: Chunk size for analysis
            output_format: Output format (json or txt)
            
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
            
            # Calculate statistics
            logger.info("Calculating audio statistics")
            
            rms = self._calculate_rms(samples)
            peak = self._calculate_peak(samples)
            
            chunk_samples = int(audio.frame_rate * chunk_size_ms / 1000)
            dynamic_range = self._calculate_dynamic_range(samples, chunk_samples)
            
            silence_ratio = self._calculate_silence_ratio(audio, silence_threshold, chunk_size_ms)
            vad_stats = self._calculate_vad(audio, vad_threshold, chunk_size_ms)
            
            # Build statistics dict
            stats = {
                "file": {
                    "name": input_path.name,
                    "path": str(input_path),
                    "duration_seconds": len(audio) / 1000,
                    "duration_ms": len(audio),
                    "format": input_path.suffix.lstrip("."),
                    "sample_rate": audio.frame_rate,
                    "channels": audio.channels,
                    "sample_width_bits": audio.sample_width * 8,
                },
                "levels": {
                    "rms": rms,
                    "rms_db": self._calculate_rms_db(rms),
                    "peak": peak,
                    "peak_db": self._calculate_peak_db(peak),
                    "dynamic_range_db": dynamic_range,
                    "overall_dbfs": audio.dBFS,
                },
                "silence": {
                    "ratio": silence_ratio,
                    "percentage": silence_ratio * 100,
                    "threshold_dbfs": silence_threshold,
                    "chunk_size_ms": chunk_size_ms,
                },
                "vad": {
                    **vad_stats,
                    "threshold_dbfs": vad_threshold,
                },
                "analysis": {
                    "processor": self.name,
                    "version": self.version,
                    "processing_time_ms": 0,  # Will be updated
                },
            }
            
            # Generate output
            ext = "json" if output_format == "json" else "txt"
            output_path = output_dir / f"{input_path.stem}_stats.{ext}"
            
            output_content = self._format_output(stats, output_format)
            
            elapsed_ms = (time.time() - start_time) * 1000
            stats["analysis"]["processing_time_ms"] = elapsed_ms
            
            # Update content with final processing time
            if output_format == "json":
                output_content = json.dumps(stats, indent=2)
            
            # Write output
            output_path.write_text(output_content, encoding="utf-8")
            
            logger.info(f"Statistics saved to: {output_path}")
            
            return ProcessResult(
                success=True,
                input_path=input_path,
                output_paths=[output_path],
                metadata=stats,
                processing_time_ms=elapsed_ms,
            )
            
        except (ValidationError, ProcessingError) as e:
            logger.error(f"Analysis failed: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.exception(f"Unexpected error during analysis: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=f"Unexpected error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )
