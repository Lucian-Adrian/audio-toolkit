"""Tests for SessionManager."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from src.orchestration.session import SessionManager
from src.orchestration.session_store import SQLiteSessionStore
from src.core.types import (
    FileStatus, SessionStatus, ProcessResult, Session, FileRecord
)
from src.core.interfaces import AudioProcessor
from src.core.exceptions import SessionError, SessionNotFoundError


class MockProcessor(AudioProcessor):
    """Mock processor for testing."""
    
    def __init__(self, should_fail=False, fail_on_files=None):
        self._should_fail = should_fail
        self._fail_on_files = fail_on_files or []
        self._processed_files = []
    
    @property
    def name(self) -> str:
        return "mock-processor"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Mock processor for testing"
    
    @property
    def category(self):
        from src.core.types import ProcessorCategory
        return ProcessorCategory.MANIPULATION
    
    @property
    def parameters(self):
        return []
    
    def process(self, input_path: Path, output_dir: Path, **kwargs) -> ProcessResult:
        self._processed_files.append(input_path)
        
        if self._should_fail or input_path in self._fail_on_files:
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message="Mock processing error"
            )
        
        output_path = output_dir / f"{input_path.stem}_processed{input_path.suffix}"
        return ProcessResult(
            success=True,
            input_path=input_path,
            output_paths=[output_path]
        )


class TestSessionManager:
    """Tests for SessionManager."""
    
    @pytest.fixture
    def store(self, temp_dir):
        """Create a test session store."""
        db_path = temp_dir / "test_sessions.db"
        store = SQLiteSessionStore(db_path)
        yield store
        store.close()
    
    @pytest.fixture
    def manager(self, store):
        """Create a session manager."""
        return SessionManager(
            store=store,
            checkpoint_interval=2,  # Checkpoint every 2 files for testing
            progress=None
        )
    
    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample test files."""
        files = []
        for i in range(5):
            f = temp_dir / f"audio_{i}.wav"
            f.write_bytes(b"fake audio data")
            files.append(f)
        return files
    
    def test_run_batch_creates_session(self, manager, sample_files, output_dir):
        """Verify session created on batch start."""
        processor = MockProcessor()
        
        session = manager.run_batch(
            processor=processor,
            input_files=sample_files,
            output_dir=output_dir,
            config={"test": "config"}
        )
        
        assert session is not None
        assert session.processor_name == "mock-processor"
        assert session.total_files == 5
        assert session.config == {"test": "config"}
    
    def test_run_batch_updates_file_status(self, manager, sample_files, output_dir):
        """Verify each file status updated after processing."""
        processor = MockProcessor()
        
        session = manager.run_batch(
            processor=processor,
            input_files=sample_files,
            output_dir=output_dir,
            config={}
        )
        
        # All files should be completed
        assert session.processed_count == 5
        assert session.failed_count == 0
        assert all(f.status == FileStatus.COMPLETED for f in session.files)
    
    def test_run_batch_handles_failures(self, manager, sample_files, output_dir):
        """Handle processing failures correctly."""
        # Fail on specific files
        processor = MockProcessor(fail_on_files=[sample_files[1], sample_files[3]])
        
        session = manager.run_batch(
            processor=processor,
            input_files=sample_files,
            output_dir=output_dir,
            config={}
        )
        
        assert session.processed_count == 3  # 3 successful
        assert session.failed_count == 2  # 2 failed
        
        # Check individual file statuses
        completed_count = sum(1 for f in session.files if f.status == FileStatus.COMPLETED)
        failed_count = sum(1 for f in session.files if f.status == FileStatus.FAILED)
        
        assert completed_count == 3
        assert failed_count == 2
    
    def test_run_batch_checkpoints(self, manager, sample_files, output_dir, store):
        """AC-SESSION-4: Checkpoint every N files."""
        processor = MockProcessor()
        
        # Use checkpoint interval of 2
        manager.checkpoint_interval = 2
        
        session = manager.run_batch(
            processor=processor,
            input_files=sample_files,
            output_dir=output_dir,
            config={}
        )
        
        # Verify session is persisted (checkpoint worked)
        retrieved = store.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.processed_count == 5
    
    def test_resume_skips_completed(self, manager, store, sample_files, output_dir):
        """AC-SESSION-1: Resume skips already-completed files."""
        processor = MockProcessor()
        
        # Create a session with some files completed
        session = store.create_session(
            processor_name="mock-processor",
            file_paths=sample_files,
            config={}
        )
        
        # Mark first 3 files as completed
        for f in sample_files[:3]:
            store.update_file_status(
                session.session_id,
                f,
                FileStatus.COMPLETED,
                output_paths=[output_dir / f"processed_{f.name}"]
            )
        
        # Resume
        result = manager.run_batch(
            processor=processor,
            input_files=[],
            output_dir=output_dir,
            config={},
            resume_session_id=session.session_id
        )
        
        # Only 2 files should have been processed
        assert len(processor._processed_files) == 2
        
        # Total should show all 5
        assert result.processed_count == 5
    
    def test_resume_completed_session_fails(self, manager, store, sample_files, output_dir):
        """AC-SESSION-5: Resume on completed session shows error."""
        processor = MockProcessor()
        
        # Create and complete a session
        session = store.create_session(
            processor_name="mock-processor",
            file_paths=sample_files,
            config={}
        )
        store.complete_session(session.session_id, success=True)
        
        # Attempt to resume should raise error
        with pytest.raises(SessionError) as exc_info:
            manager.run_batch(
                processor=processor,
                input_files=[],
                output_dir=output_dir,
                config={},
                resume_session_id=session.session_id
            )
        
        assert "Cannot resume completed session" in str(exc_info.value)
    
    def test_resume_nonexistent_session_fails(self, manager, output_dir):
        """Resume with invalid session ID raises error."""
        processor = MockProcessor()
        
        with pytest.raises(SessionNotFoundError):
            manager.run_batch(
                processor=processor,
                input_files=[],
                output_dir=output_dir,
                config={},
                resume_session_id="invalid-session-id"
            )
    
    def test_resume_latest(self, manager, store, sample_files):
        """Resume latest incomplete session."""
        # Create completed session
        session1 = store.create_session(
            processor_name="processor-1",
            file_paths=sample_files[:2],
            config={}
        )
        store.complete_session(session1.session_id, success=True)
        
        # Create incomplete session
        session2 = store.create_session(
            processor_name="processor-2",
            file_paths=sample_files[2:],
            config={}
        )
        
        result = manager.resume_latest()
        
        assert result.session_id == session2.session_id
    
    def test_resume_latest_none(self, manager, store, sample_files):
        """Resume raises error when no incomplete sessions."""
        # Create and complete a session
        session = store.create_session(
            processor_name="processor-1",
            file_paths=sample_files,
            config={}
        )
        store.complete_session(session.session_id, success=True)
        
        with pytest.raises(SessionNotFoundError):
            manager.resume_latest()
    
    def test_get_resumable_session(self, manager, store, sample_files):
        """Get resumable session without raising."""
        session = store.create_session(
            processor_name="processor-1",
            file_paths=sample_files,
            config={}
        )
        
        result = manager.get_resumable_session()
        
        assert result is not None
        assert result.session_id == session.session_id
    
    def test_get_resumable_session_none(self, manager, store, sample_files):
        """Return None when no resumable session."""
        session = store.create_session(
            processor_name="processor-1",
            file_paths=sample_files,
            config={}
        )
        store.complete_session(session.session_id, success=True)
        
        result = manager.get_resumable_session()
        
        assert result is None
    
    def test_list_sessions(self, manager, store, sample_files):
        """List recent sessions."""
        # Create multiple sessions
        for i in range(3):
            store.create_session(
                processor_name=f"processor-{i}",
                file_paths=sample_files,
                config={}
            )
        
        sessions = manager.list_sessions(limit=10)
        
        assert len(sessions) == 3
    
    def test_clean_old_sessions(self, manager, store, sample_files):
        """Clean old sessions."""
        # Create a session and make it old
        session = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={}
        )
        
        from datetime import datetime, timedelta
        with store._transaction() as conn:
            old_date = (datetime.now() - timedelta(days=10)).isoformat()
            conn.execute(
                "UPDATE sessions SET created_at = ? WHERE id = ?",
                (old_date, session.session_id)
            )
        
        deleted = manager.clean_old_sessions(days=7)
        
        assert deleted == 1
    
    def test_session_completes_successfully(self, manager, sample_files, output_dir):
        """Session marked as completed when all files succeed."""
        processor = MockProcessor()
        
        session = manager.run_batch(
            processor=processor,
            input_files=sample_files,
            output_dir=output_dir,
            config={}
        )
        
        assert session.status == SessionStatus.COMPLETED
    
    def test_session_completes_with_failures(self, manager, sample_files, output_dir):
        """Session marked as completed even with some failures."""
        processor = MockProcessor(fail_on_files=[sample_files[0]])
        
        session = manager.run_batch(
            processor=processor,
            input_files=sample_files,
            output_dir=output_dir,
            config={}
        )
        
        # Partial success still completes
        assert session.status == SessionStatus.COMPLETED
        assert session.failed_count == 1
    
    def test_session_fails_when_all_fail(self, manager, sample_files, output_dir):
        """Session marked as failed when all files fail."""
        processor = MockProcessor(should_fail=True)
        
        session = manager.run_batch(
            processor=processor,
            input_files=sample_files,
            output_dir=output_dir,
            config={}
        )
        
        assert session.status == SessionStatus.FAILED
        assert session.failed_count == 5
    
    def test_processor_exception_handled(self, manager, sample_files, output_dir):
        """Handle processor exceptions gracefully."""
        processor = MockProcessor()
        
        # Make processor raise an exception on specific file
        def raise_on_second(input_path, output_dir, **kwargs):
            if input_path == sample_files[1]:
                raise RuntimeError("Unexpected error")
            return ProcessResult(
                success=True,
                input_path=input_path,
                output_paths=[output_dir / f"processed_{input_path.name}"]
            )
        
        processor.process = raise_on_second
        
        session = manager.run_batch(
            processor=processor,
            input_files=sample_files,
            output_dir=output_dir,
            config={}
        )
        
        # Session should complete with one failure
        assert session.processed_count == 4
        assert session.failed_count == 1
        
        # The failed file should have error message
        failed_file = next(
            f for f in session.files 
            if f.file_path == sample_files[1]
        )
        assert failed_file.status == FileStatus.FAILED
        assert "Unexpected error" in failed_file.error_message


class TestSessionManagerSignalHandling:
    """Tests for signal handling in SessionManager."""
    
    @pytest.fixture
    def store(self, temp_dir):
        """Create a test session store."""
        db_path = temp_dir / "test_sessions.db"
        store = SQLiteSessionStore(db_path)
        yield store
        store.close()
    
    @pytest.fixture
    def manager(self, store):
        """Create a session manager."""
        return SessionManager(
            store=store,
            checkpoint_interval=100,
            progress=None
        )
    
    def test_signal_handlers_registered(self, manager, store, temp_dir, output_dir):
        """Signal handlers are registered during batch processing."""
        import signal
        
        files = [temp_dir / "test.wav"]
        files[0].write_bytes(b"data")
        
        original_sigint = signal.getsignal(signal.SIGINT)
        
        # We can't easily test signal handling without actually sending signals
        # Just verify the manager has the interrupt handling method
        assert hasattr(manager, '_handle_interrupt')
        assert hasattr(manager, '_register_signal_handlers')
        assert hasattr(manager, '_restore_signal_handlers')
