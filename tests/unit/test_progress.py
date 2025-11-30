"""Unit tests for progress reporting utilities."""

import pytest
from io import StringIO

from src.utils.progress import (
    RichProgressReporter,
    SilentProgressReporter,
    create_progress_reporter,
)
from src.core.interfaces import ProgressReporter


class TestRichProgressReporter:
    """Tests for RichProgressReporter class."""
    
    def test_init(self):
        """Test RichProgressReporter initialization."""
        reporter = RichProgressReporter()
        
        assert reporter._progress is None
        assert reporter._task_id is None
        assert reporter._total == 0
    
    def test_start(self):
        """Test starting progress tracking."""
        reporter = RichProgressReporter()
        
        reporter.start(total=100, description="Test")
        
        assert reporter._progress is not None
        assert reporter._task_id is not None
        assert reporter._total == 100
        
        # Cleanup
        reporter.complete()
    
    def test_update(self):
        """Test updating progress."""
        reporter = RichProgressReporter()
        reporter.start(total=100, description="Test")
        
        # Should not raise
        reporter.update(50)
        reporter.update(75, message="Processing...")
        
        reporter.complete()
    
    def test_update_without_start(self):
        """Test update without start does nothing."""
        reporter = RichProgressReporter()
        
        # Should not raise
        reporter.update(50)
    
    def test_advance(self):
        """Test advancing progress."""
        reporter = RichProgressReporter()
        reporter.start(total=100, description="Test")
        
        # Should not raise
        reporter.advance(1)
        reporter.advance(10)
        
        reporter.complete()
    
    def test_advance_without_start(self):
        """Test advance without start does nothing."""
        reporter = RichProgressReporter()
        
        # Should not raise
        reporter.advance(5)
    
    def test_complete(self):
        """Test completing progress."""
        reporter = RichProgressReporter()
        reporter.start(total=100, description="Test")
        
        reporter.complete()
        
        # Progress should be stopped
        assert reporter._progress is None or not reporter._progress.live.is_started
    
    def test_complete_with_message(self):
        """Test completing with message."""
        reporter = RichProgressReporter()
        reporter.start(total=100, description="Test")
        
        # Should not raise
        reporter.complete(message="Done!")
    
    def test_complete_without_start(self):
        """Test complete without start does nothing."""
        reporter = RichProgressReporter()
        
        # Should not raise
        reporter.complete()
    
    def test_error(self):
        """Test error reporting."""
        reporter = RichProgressReporter()
        reporter.start(total=100, description="Test")
        
        # Should not raise
        reporter.error("Something went wrong")
    
    def test_error_without_start(self):
        """Test error without start still prints."""
        reporter = RichProgressReporter()
        
        # Should not raise
        reporter.error("Error message")


class TestSilentProgressReporter:
    """Tests for SilentProgressReporter class."""
    
    def test_implements_interface(self):
        """Test SilentProgressReporter implements ProgressReporter."""
        reporter = SilentProgressReporter()
        
        assert isinstance(reporter, ProgressReporter)
    
    def test_start(self):
        """Test start does nothing."""
        reporter = SilentProgressReporter()
        
        # Should not raise
        reporter.start(100, "Test")
    
    def test_update(self):
        """Test update does nothing."""
        reporter = SilentProgressReporter()
        
        # Should not raise
        reporter.update(50, "Message")
    
    def test_complete(self):
        """Test complete does nothing."""
        reporter = SilentProgressReporter()
        
        # Should not raise
        reporter.complete("Done")
    
    def test_error(self):
        """Test error does nothing."""
        reporter = SilentProgressReporter()
        
        # Should not raise
        reporter.error("Error")


class TestCreateProgressReporter:
    """Tests for create_progress_reporter function."""
    
    def test_create_rich_reporter(self):
        """Test creating non-silent reporter."""
        reporter = create_progress_reporter(silent=False)
        
        assert isinstance(reporter, RichProgressReporter)
    
    def test_create_silent_reporter(self):
        """Test creating silent reporter."""
        reporter = create_progress_reporter(silent=True)
        
        assert isinstance(reporter, SilentProgressReporter)
    
    def test_default_is_rich(self):
        """Test default is RichProgressReporter."""
        reporter = create_progress_reporter()
        
        assert isinstance(reporter, RichProgressReporter)
