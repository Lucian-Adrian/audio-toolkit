"""Base splitter class with shared functionality."""

from abc import abstractmethod
from pathlib import Path
from typing import List, Tuple

from pydub import AudioSegment

from ...core.interfaces import AudioProcessor
from ...core.types import ParameterSpec, ProcessorCategory


class BaseSplitter(AudioProcessor):
    """
    Abstract base class for audio splitters.
    
    Provides common functionality for splitting audio files into segments.
    Subclasses implement the segment calculation logic.
    """
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.MANIPULATION
    
    @abstractmethod
    def _calculate_segments(
        self,
        audio: AudioSegment,
        **kwargs
    ) -> List[Tuple[float, float]]:
        """
        Calculate segment boundaries.
        
        Args:
            audio: The AudioSegment to split
            **kwargs: Splitter-specific parameters
            
        Returns:
            List of (start_ms, end_ms) tuples
        """
        pass
    
    def _generate_segment_filename(
        self,
        input_path: Path,
        segment_index: int,
        output_dir: Path,
        output_format: str,
    ) -> Path:
        """Generate filename for a segment."""
        return output_dir / f"{input_path.stem}_segment_{segment_index:03d}.{output_format}"
