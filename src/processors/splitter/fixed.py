"""Fixed duration audio splitter."""

import time
from pathlib import Path
from typing import List, Tuple

from pydub import AudioSegment

from ...core.exceptions import ProcessingError, ValidationError
from ...core.types import ParameterSpec, ProcessResult
from ...utils.audio import export_audio, load_audio
from ...utils.file_ops import ensure_directory
from ...utils.logger import get_logger
from ...utils.validators import validate_duration, validate_input_file
from .base import BaseSplitter

logger = get_logger(__name__)


class FixedSplitter(BaseSplitter):
    """
    Splitter that divides audio into fixed-duration segments.
    
    Pure function implementation - no side effects beyond file I/O.
    """
    
    @property
    def name(self) -> str:
        return "splitter-fixed"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Split audio into fixed-duration segments"
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec(
                name="duration_ms",
                type="float",
                description="Duration of each segment in milliseconds",
                required=True,
                min_value=100.0,
            ),
            ParameterSpec(
                name="output_format",
                type="string",
                description="Output audio format",
                required=False,
                default="mp3",
                choices=["mp3", "wav", "flac", "ogg"],
            ),
            ParameterSpec(
                name="min_last_segment_ms",
                type="float",
                description="Minimum length for last segment (shorter merged with previous)",
                required=False,
                default=1000.0,
                min_value=0.0,
            ),
        ]
    
    def _calculate_segments(
        self,
        audio: AudioSegment,
        duration_ms: float,
        min_last_segment_ms: float = 1000.0,
        **kwargs
    ) -> List[Tuple[float, float]]:
        """Calculate fixed-duration segment boundaries."""
        total_duration = len(audio)
        segments = []
        start = 0.0
        
        while start < total_duration:
            end = min(start + duration_ms, total_duration)
            
            # Cleanup: merge short last segment with previous
            remaining = total_duration - end
            if 0 < remaining < min_last_segment_ms:
                end = total_duration
            
            segments.append((start, end))
            start = end
        
        return segments
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        duration_ms: float,
        output_format: str = "mp3",
        min_last_segment_ms: float = 1000.0,
        **kwargs
    ) -> ProcessResult:
        """
        Split audio file into fixed-duration segments.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output segments
            duration_ms: Duration of each segment in milliseconds
            output_format: Output audio format
            min_last_segment_ms: Minimum length for last segment
            
        Returns:
            ProcessResult with success status and output paths
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            validate_input_file(input_path)
            validate_duration(duration_ms)
            
            # Ensure output directory exists
            ensure_directory(output_dir)
            
            # Load audio
            logger.info(f"Loading audio: {input_path}")
            audio = load_audio(input_path)
            
            # Calculate segments
            segments = self._calculate_segments(
                audio,
                duration_ms=duration_ms,
                min_last_segment_ms=min_last_segment_ms,
            )
            
            logger.info(f"Splitting into {len(segments)} segments")
            
            # Export segments
            output_paths = []
            for i, (start, end) in enumerate(segments, 1):
                segment = audio[int(start):int(end)]
                output_path = self._generate_segment_filename(
                    input_path, i, output_dir, output_format
                )
                export_audio(segment, output_path, format=output_format)
                output_paths.append(output_path)
                logger.debug(f"Created segment {i}: {output_path}")
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"Split complete: {len(output_paths)} segments in {elapsed_ms:.0f}ms"
            )
            
            return ProcessResult(
                success=True,
                input_path=input_path,
                output_paths=output_paths,
                metadata={
                    "segment_count": len(output_paths),
                    "duration_ms": duration_ms,
                    "total_duration_ms": len(audio),
                },
                processing_time_ms=elapsed_ms,
            )
            
        except (ValidationError, ProcessingError) as e:
            logger.error(f"Split failed: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.exception(f"Unexpected error during split: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=f"Unexpected error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )
