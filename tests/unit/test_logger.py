"""Unit tests for logger utilities."""

import pytest
import logging
from pathlib import Path

from src.utils.logger import setup_logging, get_logger


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_setup_logging_default(self):
        """Test default logging setup."""
        logger = setup_logging()
        
        assert logger.name == "audio_toolkit"
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1
    
    def test_setup_logging_debug_level(self):
        """Test logging with DEBUG level."""
        logger = setup_logging(level=logging.DEBUG)
        
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_warning_level(self):
        """Test logging with WARNING level."""
        logger = setup_logging(level=logging.WARNING)
        
        assert logger.level == logging.WARNING
    
    def test_setup_logging_with_file_handler(self, tmp_path):
        """Test logging with file output."""
        log_file = tmp_path / "logs" / "test.log"
        
        logger = setup_logging(log_file=log_file)
        
        # File should be created via parent directory
        assert log_file.parent.exists()
        
        # Log something
        logger.info("Test message")
        
        # Should have at least 2 handlers (rich + file)
        assert len(logger.handlers) >= 2
    
    def test_setup_logging_clears_existing_handlers(self):
        """Test that setup clears existing handlers."""
        # Setup once
        logger = setup_logging()
        initial_handler_count = len(logger.handlers)
        
        # Setup again - should not accumulate handlers
        logger = setup_logging()
        
        assert len(logger.handlers) == initial_handler_count
    
    def test_setup_logging_rich_tracebacks_disabled(self):
        """Test logging with rich tracebacks disabled."""
        logger = setup_logging(rich_tracebacks=False)
        
        assert logger is not None
        # Just verify it doesn't crash


class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_get_logger_default(self):
        """Test getting default logger."""
        logger = get_logger()
        
        assert logger.name == "audio_toolkit"
    
    def test_get_logger_custom_name(self):
        """Test getting logger with custom name."""
        logger = get_logger("custom.module")
        
        assert logger.name == "custom.module"
    
    def test_get_logger_returns_same_instance(self):
        """Test that same name returns same logger."""
        logger1 = get_logger("test.module")
        logger2 = get_logger("test.module")
        
        assert logger1 is logger2
