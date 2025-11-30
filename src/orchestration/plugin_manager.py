"""Plugin discovery and management system.

This module provides the PluginManager class for discovering, loading, and managing
audio processors from both built-in sources and third-party packages via entry_points.

Plugin discovery follows this order:
1. Built-in processors from src/processors/
2. Third-party plugins via entry_points(group="audiotoolkit.plugins")

Example third-party plugin pyproject.toml:
    [project.entry-points."audiotoolkit.plugins"]
    my-processor = "my_package.processor:MyProcessor"
"""

from importlib.metadata import entry_points, EntryPoint
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Type

from ..core.exceptions import PluginError, PluginInterfaceError, PluginNotFoundError
from ..core.interfaces import AudioProcessor
from ..core.types import ProcessorCategory
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Entry point group name for audio toolkit plugins
PLUGIN_ENTRY_POINT_GROUP = "audiotoolkit.plugins"


class PluginManager:
    """
    Discovers and manages all available audio processors.
    
    This class implements a registry pattern for audio processors,
    supporting both built-in processors and third-party plugins
    discovered via Python entry points.
    
    Thread Safety:
        This class is NOT thread-safe. Plugin discovery should be
        performed once at startup before concurrent access.
    
    Usage:
        # Initialize and discover plugins
        PluginManager.discover()
        
        # Get a processor
        processor = PluginManager.get("splitter-fixed")
        
        # List all processors
        all_processors = PluginManager.list_all()
        
        # Disable a plugin
        PluginManager.disable("problematic-plugin")
    """
    
    # Class-level registries
    _processors: Dict[str, Type[AudioProcessor]] = {}
    _instances: Dict[str, AudioProcessor] = {}
    _disabled: Set[str] = set()
    _initialized: bool = False
    
    @classmethod
    def discover(cls, include_disabled: bool = False) -> None:
        """
        Load built-in and third-party processors.
        
        This method should be called once at application startup.
        It will:
        1. Clear existing registries (if re-discovering)
        2. Register all built-in processors
        3. Discover and load third-party plugins via entry_points
        
        Args:
            include_disabled: If True, also load previously disabled plugins
            
        Raises:
            No exceptions raised - errors are logged and skipped
        """
        logger.debug("Starting plugin discovery")
        
        # Clear registries (except disabled set unless include_disabled)
        cls._processors.clear()
        cls._instances.clear()
        if include_disabled:
            cls._disabled.clear()
        
        # Load built-in processors first
        cls._register_builtins()
        
        # Load third-party plugins from entry_points
        cls._discover_entry_points()
        
        cls._initialized = True
        logger.info(
            f"Plugin discovery complete: {len(cls._instances)} processors loaded, "
            f"{len(cls._disabled)} disabled"
        )
    
    @classmethod
    def _register_builtins(cls) -> None:
        """Register all built-in processors."""
        # Import built-in processors
        from ..processors.splitter import FixedSplitter
        from ..processors.converter import FormatConverter
        
        builtin_classes: List[Type[AudioProcessor]] = [
            FixedSplitter,
            FormatConverter,
        ]
        
        for processor_class in builtin_classes:
            try:
                cls._register_processor(processor_class, source="builtin")
            except Exception as e:
                logger.error(f"Failed to register builtin {processor_class.__name__}: {e}")
    
    @classmethod
    def _discover_entry_points(cls) -> None:
        """Discover and load third-party plugins via entry_points."""
        try:
            eps = entry_points(group=PLUGIN_ENTRY_POINT_GROUP)
            
            # Handle both Python 3.9 and 3.10+ API differences
            if hasattr(eps, "__iter__"):
                ep_list: Iterator[EntryPoint] = iter(eps)
            else:
                # Python 3.9 returns a dict
                ep_list = eps.get(PLUGIN_ENTRY_POINT_GROUP, [])
            
            for ep in ep_list:
                cls._load_plugin(ep)
                
        except Exception as e:
            logger.error(f"Error discovering entry points: {e}")
    
    @classmethod
    def _load_plugin(cls, ep: EntryPoint) -> None:
        """
        Load a single plugin from an entry point.
        
        Args:
            ep: The entry point to load
            
        Behavior:
            - Validates the plugin implements AudioProcessor
            - Skips disabled plugins
            - Logs and skips duplicate plugins
            - Logs and skips invalid plugins
        """
        try:
            # Check if this plugin name is disabled
            if ep.name in cls._disabled:
                logger.debug(f"Skipping disabled plugin: {ep.name}")
                return
            
            # Load the plugin class
            logger.debug(f"Loading plugin: {ep.name} from {ep.value}")
            plugin_class = ep.load()
            
            # Validate it's a class
            if not isinstance(plugin_class, type):
                raise PluginInterfaceError(
                    f"Entry point {ep.name} must reference a class, "
                    f"got {type(plugin_class).__name__}"
                )
            
            cls._register_processor(plugin_class, source=f"entrypoint:{ep.name}")
            
        except PluginInterfaceError as e:
            logger.warning(f"Plugin interface error for {ep.name}: {e}")
        except Exception as e:
            logger.error(f"Failed to load plugin {ep.name}: {e}")
    
    @classmethod
    def _register_processor(
        cls,
        processor_class: Type[AudioProcessor],
        source: str = "unknown"
    ) -> None:
        """
        Register a processor class.
        
        Args:
            processor_class: The processor class to register
            source: Source identifier for logging (e.g., "builtin", "entrypoint:name")
            
        Raises:
            PluginInterfaceError: If the class doesn't implement AudioProcessor
        """
        # Instantiate to get name and validate interface
        try:
            instance = processor_class()
        except Exception as e:
            raise PluginInterfaceError(
                f"Failed to instantiate {processor_class.__name__}: {e}"
            )
        
        # Validate it's an AudioProcessor
        if not isinstance(instance, AudioProcessor):
            raise PluginInterfaceError(
                f"{processor_class.__name__} must implement AudioProcessor interface"
            )
        
        # Validate required properties exist and have values
        try:
            name = instance.name
            version = instance.version
            description = instance.description
            
            if not name or not isinstance(name, str):
                raise PluginInterfaceError(f"Processor must have a valid 'name' property")
            if not version or not isinstance(version, str):
                raise PluginInterfaceError(f"Processor must have a valid 'version' property")
            if not description or not isinstance(description, str):
                raise PluginInterfaceError(f"Processor must have a valid 'description' property")
                
        except AttributeError as e:
            raise PluginInterfaceError(f"Missing required property: {e}")
        
        # Check for duplicates
        if name in cls._instances:
            existing_source = "builtin" if name in ["splitter-fixed", "converter"] else "third-party"
            logger.warning(
                f"Duplicate processor '{name}' from {source} - "
                f"keeping existing from {existing_source}"
            )
            return
        
        # Check if disabled
        if name in cls._disabled:
            logger.debug(f"Skipping disabled processor: {name}")
            return
        
        # Register
        cls._processors[name] = processor_class
        cls._instances[name] = instance
        logger.debug(f"Registered processor: {name} v{version} from {source}")
    
    @classmethod
    def register(cls, processor_class: Type[AudioProcessor]) -> Type[AudioProcessor]:
        """
        Manually register a processor class.
        
        This method can be used as a decorator for runtime registration:
        
            @PluginManager.register
            class MyProcessor(AudioProcessor):
                ...
        
        Args:
            processor_class: The processor class to register
            
        Returns:
            The same class (for decorator usage)
            
        Raises:
            PluginInterfaceError: If the class doesn't implement AudioProcessor
        """
        cls._register_processor(processor_class, source="manual")
        return processor_class
    
    @classmethod
    def get(cls, name: str) -> AudioProcessor:
        """
        Get processor instance by name.
        
        Args:
            name: Unique processor name (e.g., "splitter-fixed")
            
        Returns:
            AudioProcessor instance
            
        Raises:
            PluginNotFoundError: If processor not found
        """
        if not cls._initialized:
            cls.discover()
        
        if name not in cls._instances:
            available = sorted(cls._instances.keys())
            raise PluginNotFoundError(
                f"Unknown processor: '{name}'. Available: {', '.join(available)}"
            )
        
        return cls._instances[name]
    
    @classmethod
    def get_class(cls, name: str) -> Type[AudioProcessor]:
        """
        Get processor class by name.
        
        Args:
            name: Unique processor name
            
        Returns:
            AudioProcessor class
            
        Raises:
            PluginNotFoundError: If processor not found
        """
        if not cls._initialized:
            cls.discover()
        
        if name not in cls._processors:
            available = sorted(cls._processors.keys())
            raise PluginNotFoundError(
                f"Unknown processor: '{name}'. Available: {', '.join(available)}"
            )
        
        return cls._processors[name]
    
    @classmethod
    def list_all(cls) -> Dict[str, AudioProcessor]:
        """
        Return all registered processor instances.
        
        Returns:
            Dictionary mapping processor names to instances
        """
        if not cls._initialized:
            cls.discover()
        
        return cls._instances.copy()
    
    @classmethod
    def list_by_category(
        cls,
        category: ProcessorCategory
    ) -> Dict[str, AudioProcessor]:
        """
        Return processors filtered by category.
        
        Args:
            category: The ProcessorCategory to filter by
            
        Returns:
            Dictionary of processors in the specified category
        """
        if not cls._initialized:
            cls.discover()
        
        return {
            name: proc for name, proc in cls._instances.items()
            if proc.category == category
        }
    
    @classmethod
    def list_names(cls) -> List[str]:
        """
        Return sorted list of all processor names.
        
        Returns:
            Sorted list of processor names
        """
        if not cls._initialized:
            cls.discover()
        
        return sorted(cls._instances.keys())
    
    @classmethod
    def disable(cls, name: str) -> None:
        """
        Disable a plugin (will be skipped on next discover).
        
        Args:
            name: Processor name to disable
        """
        cls._disabled.add(name)
        
        # Remove from active registries if present
        if name in cls._instances:
            del cls._instances[name]
        if name in cls._processors:
            del cls._processors[name]
        
        logger.info(f"Disabled processor: {name}")
    
    @classmethod
    def enable(cls, name: str) -> None:
        """
        Re-enable a previously disabled plugin.
        
        Note: You must call discover() again to actually load the plugin.
        
        Args:
            name: Processor name to enable
        """
        cls._disabled.discard(name)
        logger.info(f"Enabled processor: {name} (call discover() to reload)")
    
    @classmethod
    def is_disabled(cls, name: str) -> bool:
        """Check if a processor is disabled."""
        return name in cls._disabled
    
    @classmethod
    def get_disabled(cls) -> Set[str]:
        """Get set of disabled processor names."""
        return cls._disabled.copy()
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset the plugin manager to uninitialized state.
        
        This is primarily useful for testing.
        """
        cls._processors.clear()
        cls._instances.clear()
        cls._disabled.clear()
        cls._initialized = False
        logger.debug("Plugin manager reset")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if plugin discovery has been run."""
        return cls._initialized


# Module-level convenience functions
def discover() -> None:
    """Discover and load all plugins."""
    PluginManager.discover()


def get_processor(name: str) -> AudioProcessor:
    """Get a processor by name."""
    return PluginManager.get(name)


def list_processors() -> List[str]:
    """List all processor names."""
    return PluginManager.list_names()


__all__ = [
    "PluginManager",
    "PLUGIN_ENTRY_POINT_GROUP",
    "discover",
    "get_processor",
    "list_processors",
]
