"""Audio trimmer for automatic silence removal."""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.exceptions import ProcessingError, ValidationError
from ..core.interfaces import AudioProcessor
from ..core.types import ParameterSpec, ProcessorCategory, ProcessResult
from ..utils.file_ops import ensure_directory
from ..utils.logger import get_logger
from ..utils.validators import validate_input_file

logger = get_logger(__name__)

try:
    from pydub import AudioSegment
    from pydub.silence import detect_silence, detect_nonsilent
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False


class AudioTrimmer(AudioProcessor):
    """
    Audio trimmer for automatic silence detection and removal.
    
    Features:
    - Trim silence from start and end
    - Remove internal silence (optional)
    - Configurable silence threshold and minimum length
    - Padding control
    """
    
    @property
    def name(self) -> str:
        return "trimmer"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Automatically trim silence from audio files"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.VOICE
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec(
                name="mode",
                type="string",
                description="Trimming mode: 'edges' (start/end), 'all' (remove all silence)",
                required=False,
                default="edges",
                choices=["edges", "all"],
            ),
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
                name="min_silence_ms",
                type="integer",
                description="Minimum silence duration to detect (ms)",
                required=False,
                default=500,
                min_value=10,
                max_value=10000,
            ),
            ParameterSpec(
                name="padding_ms",
                type="integer",
                description="Padding to keep at start/end after trimming (ms)",
                required=False,
                default=50,
                min_value=0,
                max_value=5000,
            ),
            ParameterSpec(
                name="max_silence_ms",
                type="integer",
                description="Maximum silence to keep when mode='all' (ms)",
                required=False,
                default=300,
                min_value=0,
                max_value=5000,
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
        if not HAS_PYDUB:
            raise ProcessingError(
                "Missing required dependency: pydub. "
                "Install with: pip install pydub"
            )
    
    def _trim_edges(
        self,
        audio: "AudioSegment",
        silence_thresh: float,
        min_silence_len: int,
        padding_ms: int,
    ) -> Tuple["AudioSegment", Dict[str, Any]]:
        """
        Trim silence from start and end of audio.
        
        Returns:
            Tuple of (trimmed audio, trim info dict)
        """
        # Detect non-silent sections
        nonsilent_ranges = detect_nonsilent(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
        )
        
        if not nonsilent_ranges:
            # Entire audio is silent
            logger.warning("Audio is entirely silent")
            return audio[:0], {
                "start_trimmed_ms": len(audio),
                "end_trimmed_ms": 0,
                "total_trimmed_ms": len(audio),
            }
        
        # Get first and last non-silent ranges
        start_ms = nonsilent_ranges[0][0]
        end_ms = nonsilent_ranges[-1][1]
        
        # Apply padding
        start_ms = max(0, start_ms - padding_ms)
        end_ms = min(len(audio), end_ms + padding_ms)
        
        # Trim
        trimmed = audio[start_ms:end_ms]
        
        trim_info = {
            "start_trimmed_ms": start_ms,
            "end_trimmed_ms": len(audio) - end_ms,
            "total_trimmed_ms": (start_ms) + (len(audio) - end_ms),
            "original_duration_ms": len(audio),
            "trimmed_duration_ms": len(trimmed),
        }
        
        return trimmed, trim_info
    
    def _remove_all_silence(
        self,
        audio: "AudioSegment",
        silence_thresh: float,
        min_silence_len: int,
        max_silence_ms: int,
    ) -> Tuple["AudioSegment", Dict[str, Any]]:
        """
        Remove or reduce all internal silences.
        
        Args:
            audio: Audio segment
            silence_thresh: Silence threshold in dBFS
            min_silence_len: Minimum silence to detect (ms)
            max_silence_ms: Maximum silence to keep (ms)
            
        Returns:
            Tuple of (processed audio, info dict)
        """
        # Detect non-silent sections
        nonsilent_ranges = detect_nonsilent(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
        )
        
        if not nonsilent_ranges:
            return audio[:0], {
                "sections_found": 0,
                "silence_removed_ms": len(audio),
            }
        
        if len(nonsilent_ranges) == 1:
            # Only one section, just trim edges
            start, end = nonsilent_ranges[0]
            return audio[start:end], {
                "sections_found": 1,
                "silence_removed_ms": start + (len(audio) - end),
            }
        
        # Build output by joining non-silent sections with reduced silence
        segments = []
        total_silence_removed = 0
        
        for i, (start, end) in enumerate(nonsilent_ranges):
            # Add the non-silent section
            segments.append(audio[start:end])
            
            # Add silence between sections (if not last)
            if i < len(nonsilent_ranges) - 1:
                next_start = nonsilent_ranges[i + 1][0]
                silence_duration = next_start - end
                
                if silence_duration > max_silence_ms:
                    # Reduce silence to max_silence_ms
                    total_silence_removed += silence_duration - max_silence_ms
                    if max_silence_ms > 0:
                        # Keep some silence
                        segments.append(AudioSegment.silent(
                            duration=max_silence_ms,
                            frame_rate=audio.frame_rate,
                        ))
                else:
                    # Keep original silence
                    segments.append(audio[end:next_start])
        
        # Combine segments
        result = segments[0]
        for seg in segments[1:]:
            result = result + seg
        
        info = {
            "sections_found": len(nonsilent_ranges),
            "silence_removed_ms": total_silence_removed,
            "original_duration_ms": len(audio),
            "processed_duration_ms": len(result),
        }
        
        return result, info
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        mode: str = "edges",
        silence_threshold: float = -40.0,
        min_silence_ms: int = 500,
        padding_ms: int = 50,
        max_silence_ms: int = 300,
        output_format: str = "wav",
        **kwargs
    ) -> ProcessResult:
        """
        Trim silence from audio file.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output file
            mode: 'edges' to trim start/end, 'all' to remove all silence
            silence_threshold: Silence threshold in dBFS
            min_silence_ms: Minimum silence duration to detect
            padding_ms: Padding to keep after edge trimming
            max_silence_ms: Max silence to keep in 'all' mode
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
            
            logger.info(
                f"Trimming mode='{mode}', threshold={silence_threshold}dBFS, "
                f"min_silence={min_silence_ms}ms"
            )
            
            # Process based on mode
            if mode == "edges":
                processed, trim_info = self._trim_edges(
                    audio,
                    silence_threshold,
                    min_silence_ms,
                    padding_ms,
                )
            else:  # mode == "all"
                # First trim edges
                trimmed, edge_info = self._trim_edges(
                    audio,
                    silence_threshold,
                    min_silence_ms,
                    padding_ms=0,  # No padding for intermediate step
                )
                
                # Then remove internal silence
                processed, internal_info = self._remove_all_silence(
                    trimmed,
                    silence_threshold,
                    min_silence_ms,
                    max_silence_ms,
                )
                
                trim_info = {
                    "edge_trim": edge_info,
                    "internal_trim": internal_info,
                    "total_removed_ms": (
                        edge_info.get("total_trimmed_ms", 0) +
                        internal_info.get("silence_removed_ms", 0)
                    ),
                }
            
            # Check if we have any audio left
            if len(processed) == 0:
                logger.warning("No audio remaining after trimming")
                return ProcessResult(
                    success=False,
                    input_path=input_path,
                    error_message="Audio is entirely silent, nothing to output",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )
            
            # Export
            output_path = output_dir / f"{input_path.stem}_trimmed.{output_format}"
            logger.info(f"Exporting to: {output_path}")
            
            processed.export(output_path, format=output_format)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Calculate statistics
            original_duration = len(audio)
            processed_duration = len(processed)
            reduction_percent = (
                (original_duration - processed_duration) / original_duration * 100
                if original_duration > 0 else 0
            )
            
            return ProcessResult(
                success=True,
                input_path=input_path,
                output_paths=[output_path],
                metadata={
                    "mode": mode,
                    "silence_threshold_dbfs": silence_threshold,
                    "min_silence_ms": min_silence_ms,
                    "original_duration_ms": original_duration,
                    "processed_duration_ms": processed_duration,
                    "reduction_percent": round(reduction_percent, 1),
                    "trim_details": trim_info,
                },
                processing_time_ms=elapsed_ms,
            )
            
        except (ValidationError, ProcessingError) as e:
            logger.error(f"Trimming failed: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.exception(f"Unexpected error during trimming: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=f"Unexpected error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )
