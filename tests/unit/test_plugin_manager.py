"""Unit tests for the Plugin Manager."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from typing import List

from src.core.interfaces import AudioProcessor
from src.core.types import ParameterSpec, ProcessorCategory, ProcessResult
from src.core.exceptions import PluginNotFoundError, PluginInterfaceError
from src.orchestration.plugin_manager import (
    PluginManager,
    PLUGIN_ENTRY_POINT_GROUP,
    discover,
    get_processor,
    list_processors,
)


class MockValidProcessor(AudioProcessor):
    """Valid mock processor for testing."""
    
    @property
    def name(self) -> str:
        return "mock-processor"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "A mock processor for testing"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.AUTOMATION
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec(
                name="test_param",
                type="string",
                description="A test parameter",
                required=False,
                default="default_value",
            )
        ]
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        **kwargs
    ) -> ProcessResult:
        return ProcessResult(
            success=True,
            input_path=input_path,
            output_paths=[output_dir / input_path.name],
        )


class MockInvalidProcessor:
    """Invalid processor that doesn't implement AudioProcessor."""
    
    @property
    def name(self) -> str:
        return "invalid-processor"


class MockProcessorNoName(AudioProcessor):
    """Processor missing name property."""
    
    @property
    def name(self) -> str:
        return ""  # Empty name
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Missing name"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.AUTOMATION
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return []
    
    def process(self, input_path: Path, output_dir: Path, **kwargs) -> ProcessResult:
        return ProcessResult(success=True, input_path=input_path)


class MockProcessorRaisesOnInit(AudioProcessor):
    """Processor that raises exception during instantiation."""
    
    def __init__(self):
        raise RuntimeError("Initialization failed!")
    
    @property
    def name(self) -> str:
        return "raises-processor"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Raises on init"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.AUTOMATION
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return []
    
    def process(self, input_path: Path, output_dir: Path, **kwargs) -> ProcessResult:
        return ProcessResult(success=True, input_path=input_path)


class TestPluginManagerDiscovery:
    """Tests for plugin discovery functionality."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_discover_builtins(self):
        """All built-in processors should be discovered."""
        PluginManager.discover()
        
        processors = PluginManager.list_all()
        
        # Check built-in processors are registered
        assert "splitter-fixed" in processors
        assert "converter" in processors
    
    def test_discover_sets_initialized(self):
        """Discovery should mark the manager as initialized."""
        assert not PluginManager.is_initialized()
        
        PluginManager.discover()
        
        assert PluginManager.is_initialized()
    
    def test_discover_clears_previous_registrations(self):
        """Re-discovering should clear previous registrations."""
        PluginManager.discover()
        initial_count = len(PluginManager.list_all())
        
        # Manually register extra processor
        PluginManager.register(MockValidProcessor)
        assert len(PluginManager.list_all()) == initial_count + 1
        
        # Re-discover should reset
        PluginManager.discover()
        assert len(PluginManager.list_all()) == initial_count
    
    def test_discover_preserves_disabled_plugins(self):
        """Disabled plugins should remain disabled after re-discovery."""
        PluginManager.discover()
        PluginManager.disable("converter")
        
        PluginManager.discover()
        
        assert PluginManager.is_disabled("converter")
        assert "converter" not in PluginManager.list_all()
    
    def test_discover_with_include_disabled(self):
        """include_disabled=True should clear disabled set."""
        PluginManager.discover()
        PluginManager.disable("converter")
        
        PluginManager.discover(include_disabled=True)
        
        assert not PluginManager.is_disabled("converter")
        assert "converter" in PluginManager.list_all()


class TestPluginManagerGet:
    """Tests for getting processors."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_get_processor(self):
        """Should return processor instance by name."""
        PluginManager.discover()
        
        processor = PluginManager.get("splitter-fixed")
        
        assert processor is not None
        assert processor.name == "splitter-fixed"
        assert isinstance(processor, AudioProcessor)
    
    def test_get_unknown_processor(self):
        """EC-PLUGIN-2: Unknown processor should raise PluginNotFoundError."""
        PluginManager.discover()
        
        with pytest.raises(PluginNotFoundError) as exc_info:
            PluginManager.get("nonexistent-processor")
        
        assert "nonexistent-processor" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)
    
    def test_get_auto_discovers(self):
        """Getting processor should auto-discover if not initialized."""
        assert not PluginManager.is_initialized()
        
        processor = PluginManager.get("splitter-fixed")
        
        assert PluginManager.is_initialized()
        assert processor is not None
    
    def test_get_class(self):
        """Should return processor class by name."""
        PluginManager.discover()
        
        processor_class = PluginManager.get_class("converter")
        
        assert processor_class is not None
        assert issubclass(processor_class, AudioProcessor)
        
        # Should be able to instantiate
        instance = processor_class()
        assert instance.name == "converter"


class TestPluginManagerRegistration:
    """Tests for manual processor registration."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_manual_register(self):
        """Manually registered processors should be accessible."""
        PluginManager.discover()
        
        PluginManager.register(MockValidProcessor)
        
        processor = PluginManager.get("mock-processor")
        assert processor.name == "mock-processor"
        assert processor.version == "1.0.0"
    
    def test_register_as_decorator(self):
        """Register should work as a decorator."""
        PluginManager.discover()
        
        @PluginManager.register
        class DecoratedProcessor(AudioProcessor):
            @property
            def name(self) -> str:
                return "decorated-processor"
            
            @property
            def version(self) -> str:
                return "1.0.0"
            
            @property
            def description(self) -> str:
                return "Decorated processor"
            
            @property
            def category(self) -> ProcessorCategory:
                return ProcessorCategory.AUTOMATION
            
            @property
            def parameters(self) -> List[ParameterSpec]:
                return []
            
            def process(self, input_path: Path, output_dir: Path, **kwargs) -> ProcessResult:
                return ProcessResult(success=True, input_path=input_path)
        
        processor = PluginManager.get("decorated-processor")
        assert processor is not None
    
    def test_invalid_plugin_skipped(self):
        """EC-PLUGIN-1: Invalid plugin should be logged and skipped."""
        PluginManager.discover()
        
        with pytest.raises(PluginInterfaceError):
            PluginManager.register(MockInvalidProcessor)
        
        # Should not be in registry
        assert "invalid-processor" not in PluginManager.list_names()
    
    def test_plugin_missing_name_rejected(self):
        """Processor with empty name should be rejected."""
        PluginManager.discover()
        
        with pytest.raises(PluginInterfaceError) as exc_info:
            PluginManager.register(MockProcessorNoName)
        
        assert "name" in str(exc_info.value).lower()
    
    def test_plugin_raising_on_init_rejected(self):
        """Processor that raises on init should be rejected."""
        PluginManager.discover()
        
        with pytest.raises(PluginInterfaceError) as exc_info:
            PluginManager.register(MockProcessorRaisesOnInit)
        
        assert "instantiate" in str(exc_info.value).lower()
    
    def test_duplicate_plugin_warns_and_keeps_first(self):
        """Duplicate plugin names should warn and keep first registration."""
        PluginManager.discover()
        
        # Register first
        PluginManager.register(MockValidProcessor)
        first_processor = PluginManager.get("mock-processor")
        
        # Create duplicate with different version
        class DuplicateProcessor(MockValidProcessor):
            @property
            def version(self) -> str:
                return "2.0.0"
        
        # Register duplicate - should log warning but not raise
        PluginManager._register_processor(DuplicateProcessor, source="test")
        
        # First registration should be kept
        processor = PluginManager.get("mock-processor")
        assert processor.version == "1.0.0"


class TestPluginManagerListing:
    """Tests for listing processors."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_list_all(self):
        """Should return all registered processors."""
        PluginManager.discover()
        
        processors = PluginManager.list_all()
        
        assert isinstance(processors, dict)
        assert len(processors) >= 2  # At least builtins
        assert all(isinstance(p, AudioProcessor) for p in processors.values())
    
    def test_list_all_returns_copy(self):
        """list_all should return a copy to prevent modification."""
        PluginManager.discover()
        
        processors = PluginManager.list_all()
        processors.clear()
        
        # Original should be unaffected
        assert len(PluginManager.list_all()) >= 2
    
    def test_list_names(self):
        """Should return sorted list of processor names."""
        PluginManager.discover()
        
        names = PluginManager.list_names()
        
        assert isinstance(names, list)
        assert names == sorted(names)
        assert "splitter-fixed" in names
        assert "converter" in names
    
    def test_list_by_category(self):
        """Should filter processors by category."""
        PluginManager.discover()
        
        manipulation = PluginManager.list_by_category(ProcessorCategory.MANIPULATION)
        
        assert len(manipulation) >= 2  # splitter-fixed, converter
        assert all(
            p.category == ProcessorCategory.MANIPULATION
            for p in manipulation.values()
        )


class TestPluginManagerDisabling:
    """Tests for disabling/enabling plugins."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_disable_plugin(self):
        """Disabled plugin should not be accessible."""
        PluginManager.discover()
        
        PluginManager.disable("converter")
        
        assert PluginManager.is_disabled("converter")
        assert "converter" not in PluginManager.list_all()
        
        with pytest.raises(PluginNotFoundError):
            PluginManager.get("converter")
    
    def test_enable_plugin(self):
        """Enabled plugin should be marked for reload."""
        PluginManager.discover()
        PluginManager.disable("converter")
        
        PluginManager.enable("converter")
        
        assert not PluginManager.is_disabled("converter")
    
    def test_get_disabled(self):
        """Should return set of disabled plugin names."""
        PluginManager.discover()
        PluginManager.disable("converter")
        PluginManager.disable("splitter-fixed")
        
        disabled = PluginManager.get_disabled()
        
        assert isinstance(disabled, set)
        assert "converter" in disabled
        assert "splitter-fixed" in disabled
    
    def test_get_disabled_returns_copy(self):
        """get_disabled should return a copy."""
        PluginManager.discover()
        PluginManager.disable("converter")
        
        disabled = PluginManager.get_disabled()
        disabled.clear()
        
        assert PluginManager.is_disabled("converter")


class TestPluginManagerReset:
    """Tests for reset functionality."""
    
    def test_reset_clears_all(self):
        """Reset should clear all registries."""
        PluginManager.discover()
        PluginManager.disable("converter")
        
        PluginManager.reset()
        
        assert not PluginManager.is_initialized()
        assert len(PluginManager._processors) == 0
        assert len(PluginManager._instances) == 0
        assert len(PluginManager._disabled) == 0


class TestPluginManagerEntryPoints:
    """Tests for entry point discovery."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    @patch('src.orchestration.plugin_manager.entry_points')
    def test_load_plugin_from_entry_point(self, mock_entry_points):
        """Should load plugin from entry point."""
        # Create mock entry point
        mock_ep = MagicMock()
        mock_ep.name = "test-plugin"
        mock_ep.value = "test_module:TestProcessor"
        mock_ep.load.return_value = MockValidProcessor
        
        mock_entry_points.return_value = [mock_ep]
        
        PluginManager.discover()
        
        # MockValidProcessor should be loaded
        assert "mock-processor" in PluginManager.list_names()
    
    @patch('src.orchestration.plugin_manager.entry_points')
    def test_invalid_entry_point_skipped(self, mock_entry_points):
        """Invalid entry point should be skipped."""
        # Create mock entry point that returns non-class
        mock_ep = MagicMock()
        mock_ep.name = "bad-plugin"
        mock_ep.value = "bad_module:not_a_class"
        mock_ep.load.return_value = "not a class"
        
        mock_entry_points.return_value = [mock_ep]
        
        # Should not raise
        PluginManager.discover()
        
        # Built-ins should still be registered
        assert "splitter-fixed" in PluginManager.list_names()
    
    @patch('src.orchestration.plugin_manager.entry_points')
    def test_entry_point_load_error_handled(self, mock_entry_points):
        """Entry point load errors should be handled gracefully."""
        mock_ep = MagicMock()
        mock_ep.name = "error-plugin"
        mock_ep.value = "error_module:ErrorProcessor"
        mock_ep.load.side_effect = ImportError("Module not found")
        
        mock_entry_points.return_value = [mock_ep]
        
        # Should not raise
        PluginManager.discover()
        
        # Built-ins should still be registered
        assert "splitter-fixed" in PluginManager.list_names()


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_discover_function(self):
        """Module-level discover should work."""
        discover()
        
        assert PluginManager.is_initialized()
    
    def test_get_processor_function(self):
        """Module-level get_processor should work."""
        discover()
        
        processor = get_processor("splitter-fixed")
        
        assert processor.name == "splitter-fixed"
    
    def test_list_processors_function(self):
        """Module-level list_processors should work."""
        discover()
        
        names = list_processors()
        
        assert "splitter-fixed" in names
        assert "converter" in names


class TestPluginManagerConcurrency:
    """Tests for thread safety considerations."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_get_before_discover_auto_discovers(self):
        """Getting processor before discover should auto-discover."""
        processor = PluginManager.get("splitter-fixed")
        
        assert processor is not None
        assert PluginManager.is_initialized()
    
    def test_list_all_before_discover_auto_discovers(self):
        """Listing processors before discover should auto-discover."""
        processors = PluginManager.list_all()
        
        assert len(processors) >= 2
        assert PluginManager.is_initialized()


# Entry point group constant test
def test_entry_point_group_constant():
    """Entry point group should be defined correctly."""
    assert PLUGIN_ENTRY_POINT_GROUP == "audiotoolkit.plugins"
