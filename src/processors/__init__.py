"""Audio processors registry and factory."""

from typing import Dict, Type, Optional
from ..core.interfaces import AudioProcessor, AudioSplitter
from .converter import AudioConverter
from .splitter.base import BaseSplitter
from .splitter.fixed import FixedDurationSplitter
from ..core.exceptions import ConfigurationError
from ..utils.logger import logger


class ProcessorRegistry:
    """Registry for audio processors."""

    def __init__(self):
        self._processors: Dict[str, Type[AudioProcessor]] = {}
        self._splitters: Dict[str, Type[AudioSplitter]] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register default processors."""
        self.register_processor('converter', AudioConverter)
        self.register_splitter('base', BaseSplitter)
        self.register_splitter('fixed', FixedDurationSplitter)

    def register_processor(self, name: str, processor_class: Type[AudioProcessor]):
        """Register an audio processor."""
        self._processors[name] = processor_class
        logger.debug(f"Registered processor: {name}")

    def register_splitter(self, name: str, splitter_class: Type[AudioSplitter]):
        """Register an audio splitter."""
        self._splitters[name] = splitter_class
        logger.debug(f"Registered splitter: {name}")

    def get_processor(self, name: str) -> Type[AudioProcessor]:
        """Get a processor class by name."""
        if name not in self._processors:
            raise ConfigurationError(f"Unknown processor: {name}")
        return self._processors[name]

    def get_splitter(self, name: str) -> Type[AudioSplitter]:
        """Get a splitter class by name."""
        if name not in self._splitters:
            raise ConfigurationError(f"Unknown splitter: {name}")
        return self._splitters[name]

    def list_processors(self) -> list:
        """List available processors."""
        return list(self._processors.keys())

    def list_splitters(self) -> list:
        """List available splitters."""
        return list(self._splitters.keys())


# Global registry instance
registry = ProcessorRegistry()
