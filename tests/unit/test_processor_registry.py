"""Unit tests for processor registry."""

import pytest

from src.processors import (
    register_processor,
    get_processor,
    get_processor_class,
    list_processors,
    FixedSplitter,
    FormatConverter,
)
from src.core.interfaces import AudioProcessor
from src.core.exceptions import PluginNotFoundError


class TestProcessorRegistry:
    """Tests for processor registry functions."""
    
    def test_list_processors(self):
        """Test listing all registered processors."""
        processors = list_processors()
        
        assert "splitter-fixed" in processors
        assert "converter" in processors
        assert processors == sorted(processors)  # Should be sorted
    
    def test_get_processor_class(self):
        """Test getting processor class by name."""
        splitter_class = get_processor_class("splitter-fixed")
        converter_class = get_processor_class("converter")
        
        assert splitter_class == FixedSplitter
        assert converter_class == FormatConverter
    
    def test_get_processor_class_not_found(self):
        """Test getting unknown processor class raises error."""
        with pytest.raises(PluginNotFoundError) as exc_info:
            get_processor_class("nonexistent-processor")
        
        assert "Unknown processor" in str(exc_info.value)
        assert "nonexistent-processor" in str(exc_info.value)
    
    def test_get_processor_creates_instance(self):
        """Test get_processor returns new instance each time."""
        splitter1 = get_processor("splitter-fixed")
        splitter2 = get_processor("splitter-fixed")
        
        assert splitter1 is not splitter2
        assert isinstance(splitter1, FixedSplitter)
        assert isinstance(splitter2, FixedSplitter)
    
    def test_get_processor_not_found(self):
        """Test getting unknown processor raises error."""
        with pytest.raises(PluginNotFoundError) as exc_info:
            get_processor("nonexistent")
        
        assert "Unknown processor" in str(exc_info.value)
        assert "Available" in str(exc_info.value)
