"""Base audio splitter implementation."""

from abc import ABC
from pathlib import Path
from typing import List
from ...core.types import AudioFile, SplitConfig, SplitResult
from ...core.interfaces import AudioSplitter
from ...core.exceptions import AudioProcessingError
from ...utils.audio import extract_audio_segment
from ...utils.logger import logger


class BaseSplitter(AudioSplitter, ABC):
    """Base class for audio splitters."""

    def split(self, audio_file: AudioFile, config: SplitConfig) -> SplitResult:
        """Split an audio file according to the configuration."""
        try:
            start_time = 0.0
            output_files = []

            segments = self._get_segments(audio_file, config)

            for i, (start, end) in enumerate(segments):
                output_path = self._get_output_path(audio_file.path, config.output_prefix, i)
                extract_audio_segment(audio_file.path, start, end, output_path)

                output_audio = AudioFile(
                    path=output_path,
                    format=output_path.suffix[1:].lower(),
                    duration=end - start,
                    sample_rate=audio_file.sample_rate,
                    channels=audio_file.channels,
                    bitrate=audio_file.bitrate
                )
                output_files.append(output_audio)

            return SplitResult(
                input_file=audio_file,
                output_files=output_files,
                success=True,
                processing_time=0.0  # TODO: measure time
            )

        except Exception as e:
            logger.error(f"Failed to split audio file {audio_file.path}: {e}")
            return SplitResult(
                input_file=audio_file,
                output_files=[],
                success=False,
                error_message=str(e),
                processing_time=0.0
            )

    def _get_segments(self, audio_file: AudioFile, config: SplitConfig) -> List[tuple]:
        """Get the segments to split. Override in subclasses."""
        raise NotImplementedError

    def _get_output_path(self, input_path: Path, prefix: str, index: int) -> Path:
        """Generate output path for a segment."""
        stem = input_path.stem
        suffix = input_path.suffix
        return input_path.parent / f"{stem}_{prefix}_{index:03d}{suffix}"