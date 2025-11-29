"""Fixed duration audio splitter."""

from typing import List
from ...core.types import AudioFile, SplitConfig
from .base import BaseSplitter


class FixedDurationSplitter(BaseSplitter):
    """Splitter that divides audio into fixed-duration segments."""

    def _get_segments(self, audio_file: AudioFile, config: SplitConfig) -> List[tuple]:
        """Get fixed-duration segments."""
        if not config.duration:
            raise ValueError("Duration must be specified for fixed splitting")

        duration = config.duration
        total_duration = audio_file.duration
        segments = []

        start_time = 0.0
        while start_time < total_duration:
            end_time = min(start_time + duration, total_duration)
            segments.append((start_time, end_time))
            start_time = end_time

        return segments