"""Processor registry and factory."""

from typing import Dict, List, Optional, Type

from ..core.exceptions import PluginNotFoundError
from ..core.interfaces import AudioProcessor
from .converter import FormatConverter
from .splitter import FixedSplitter

# Processor registry
_processors: Dict[str, Type[AudioProcessor]] = {}


def register_processor(processor_class: Type[AudioProcessor]) -> Type[AudioProcessor]:
    """
    Register a processor class.
    
    Can be used as a decorator:
        @register_processor
        class MyProcessor(AudioProcessor):
            ...
    
    Args:
        processor_class: The processor class to register
        
    Returns:
        The same class (for decorator usage)
    """
    instance = processor_class()
    _processors[instance.name] = processor_class
    return processor_class


def get_processor(name: str) -> AudioProcessor:
    """
    Get a processor instance by name.
    
    Args:
        name: Processor name
        
    Returns:
        Processor instance
        
    Raises:
        PluginNotFoundError: If processor not found
    """
    if name not in _processors:
        available = ", ".join(sorted(_processors.keys()))
        raise PluginNotFoundError(
            f"Unknown processor: {name}. Available: {available}"
        )
    return _processors[name]()


def list_processors() -> List[str]:
    """List all registered processor names."""
    return sorted(_processors.keys())


def get_processor_class(name: str) -> Type[AudioProcessor]:
    """
    Get a processor class by name.
    
    Args:
        name: Processor name
        
    Returns:
        Processor class
        
    Raises:
        PluginNotFoundError: If processor not found
    """
    if name not in _processors:
        available = ", ".join(sorted(_processors.keys()))
        raise PluginNotFoundError(
            f"Unknown processor: {name}. Available: {available}"
        )
    return _processors[name]


# Register default processors
register_processor(FixedSplitter)
register_processor(FormatConverter)


__all__ = [
    "register_processor",
    "get_processor",
    "get_processor_class",
    "list_processors",
    "FixedSplitter",
    "FormatConverter",
]
