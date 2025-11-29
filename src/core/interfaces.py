"""Abstract interfaces for audio processing components."""

from abc import ABC, abstractmethod
from typing import List
from .types import AudioFile, ProcessingConfig, SplitConfig, ConversionResult, SplitResult


class AudioProcessor(ABC):
    """Abstract base class for audio processors."""

    @abstractmethod
    def process(self, audio_file: AudioFile, config: ProcessingConfig) -> ConversionResult:
        """Process an audio file according to the given configuration."""
        pass


class AudioSplitter(ABC):
    """Abstract base class for audio splitters."""

    @abstractmethod
    def split(self, audio_file: AudioFile, config: SplitConfig) -> SplitResult:
        """Split an audio file according to the given configuration."""
        pass


class AudioValidator(ABC):
    """Abstract base class for audio validators."""

    @abstractmethod
    def validate(self, audio_file: AudioFile) -> bool:
        """Validate an audio file."""
        pass

    @abstractmethod
    def get_validation_errors(self, audio_file: AudioFile) -> List[str]:
        """Get validation errors for an audio file."""
        pass


class ProgressReporter(ABC):
    """Abstract base class for progress reporting."""

    @abstractmethod
    def start(self, total_steps: int, description: str = ""):
        """Start progress reporting."""
        pass

    @abstractmethod
    def update(self, current_step: int):
        """Update progress."""
        pass

    @abstractmethod
    def complete(self):
        """Mark progress as complete."""
        pass
