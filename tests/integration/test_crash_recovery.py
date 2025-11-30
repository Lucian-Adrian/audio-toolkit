"""Integration tests for crash recovery functionality."""

import pytest
from pathlib import Path

from src.orchestration.session_store import SQLiteSessionStore
from src.orchestration.session import SessionManager
from src.core.types import FileStatus, SessionStatus, ProcessResult
from src.core.interfaces import AudioProcessor


class SimulatedCrashProcessor(AudioProcessor):
    """Processor that simulates a crash after N files."""
    
    def __init__(self, crash_after: int = 5):
        self.crash_after = crash_after
        self.processed_count = 0
    
    @property
    def name(self) -> str:
        return "crash-simulator"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Simulates crash for testing"
    
    @property
    def category(self):
        from src.core.types import ProcessorCategory
        return ProcessorCategory.MANIPULATION
    
    @property
    def parameters(self):
        return []
    
    def process(self, input_path: Path, output_dir: Path, **kwargs) -> ProcessResult:
        self.processed_count += 1
        
        if self.processed_count > self.crash_after:
            raise KeyboardInterrupt("Simulated crash")
        
        output_path = output_dir / f"{input_path.stem}_processed{input_path.suffix}"
        output_path.write_bytes(b"processed data")
        
        return ProcessResult(
            success=True,
            input_path=input_path,
            output_paths=[output_path]
        )


class CountingProcessor(AudioProcessor):
    """Processor that counts processed files."""
    
    def __init__(self):
        self.processed_files = []
    
    @property
    def name(self) -> str:
        return "counter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Counts processed files"
    
    @property
    def category(self):
        from src.core.types import ProcessorCategory
        return ProcessorCategory.MANIPULATION
    
    @property
    def parameters(self):
        return []
    
    def process(self, input_path: Path, output_dir: Path, **kwargs) -> ProcessResult:
        self.processed_files.append(input_path)
        
        output_path = output_dir / f"{input_path.stem}_processed{input_path.suffix}"
        output_path.write_bytes(b"processed data")
        
        return ProcessResult(
            success=True,
            input_path=input_path,
            output_paths=[output_path]
        )


class TestCrashRecovery:
    """Integration tests for crash recovery functionality."""
    
    @pytest.fixture
    def db_path(self, temp_dir):
        """Create a persistent database path."""
        return temp_dir / "sessions.db"
    
    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create 10 sample test files."""
        files = []
        for i in range(10):
            f = temp_dir / f"audio_{i:02d}.wav"
            f.write_bytes(b"fake audio data " + str(i).encode())
            files.append(f)
        return files
    
    def test_crash_and_resume(self, db_path, sample_files, output_dir):
        """
        Simulate crash at file 5 of 10.
        Resume should process only files 5-10.
        """
        # Phase 1: Process until "crash" at file 5
        store1 = SQLiteSessionStore(db_path)
        manager1 = SessionManager(
            store=store1,
            checkpoint_interval=1,  # Checkpoint after each file
            progress=None
        )
        
        # Use a processor that "crashes" after 5 files
        crash_processor = SimulatedCrashProcessor(crash_after=5)
        
        session_id = None
        try:
            session = manager1.run_batch(
                processor=crash_processor,
                input_files=sample_files,
                output_dir=output_dir,
                config={"test": "value"}
            )
        except KeyboardInterrupt:
            # Get session ID before closing
            sessions = store1.list_sessions(limit=1)
            if sessions:
                session_id = sessions[0].session_id
        finally:
            store1.close()
        
        # Verify 5 files were processed before crash
        assert crash_processor.processed_count == 6  # Crashed on 6th
        
        # Phase 2: Resume and complete
        store2 = SQLiteSessionStore(db_path)
        manager2 = SessionManager(
            store=store2,
            checkpoint_interval=1,
            progress=None
        )
        
        # Get the incomplete session
        incomplete = store2.get_latest_incomplete()
        assert incomplete is not None
        
        # Count pending files
        pending = store2.get_pending_files(incomplete.session_id)
        # Should have remaining files pending (those that weren't completed)
        assert len(pending) >= 4  # At least 4 files should be pending
        
        # Resume with a working processor
        resume_processor = CountingProcessor()
        
        result = manager2.run_batch(
            processor=resume_processor,
            input_files=[],
            output_dir=output_dir,
            config={},
            resume_session_id=incomplete.session_id
        )
        
        store2.close()
        
        # Verify only remaining files were processed
        assert len(resume_processor.processed_files) == len(pending)
        
        # Verify session is now complete
        assert result.status == SessionStatus.COMPLETED
        assert result.total_files == 10
    
    def test_full_batch_with_checkpointing(self, db_path, sample_files, output_dir):
        """Full batch processes all files with regular checkpoints."""
        store = SQLiteSessionStore(db_path)
        manager = SessionManager(
            store=store,
            checkpoint_interval=3,  # Checkpoint every 3 files
            progress=None
        )
        
        processor = CountingProcessor()
        
        session = manager.run_batch(
            processor=processor,
            input_files=sample_files,
            output_dir=output_dir,
            config={"batch": "test"}
        )
        
        store.close()
        
        # All files processed
        assert len(processor.processed_files) == 10
        assert session.status == SessionStatus.COMPLETED
        assert session.processed_count == 10
        assert session.failed_count == 0
    
    def test_resume_preserves_config(self, db_path, sample_files, output_dir):
        """Resumed session uses original configuration."""
        # Create initial session
        store1 = SQLiteSessionStore(db_path)
        session = store1.create_session(
            processor_name="test-processor",
            file_paths=sample_files,
            config={
                "format": "mp3",
                "bitrate": "192k",
                "nested": {"key": "value"}
            }
        )
        
        # Complete half the files
        for f in sample_files[:5]:
            store1.update_file_status(
                session.session_id,
                f,
                FileStatus.COMPLETED,
                output_paths=[output_dir / f"out_{f.name}"]
            )
        
        store1.checkpoint(session.session_id)
        store1.close()
        
        # Reopen and verify config preserved
        store2 = SQLiteSessionStore(db_path)
        
        retrieved = store2.get_session(session.session_id)
        
        assert retrieved.config["format"] == "mp3"
        assert retrieved.config["bitrate"] == "192k"
        assert retrieved.config["nested"]["key"] == "value"
        
        store2.close()
    
    def test_multiple_sessions_independence(self, db_path, sample_files, output_dir):
        """Multiple sessions don't interfere with each other."""
        store = SQLiteSessionStore(db_path)
        
        # Create two sessions
        session1 = store.create_session(
            processor_name="processor-1",
            file_paths=sample_files[:5],
            config={"session": 1}
        )
        
        session2 = store.create_session(
            processor_name="processor-2",
            file_paths=sample_files[5:],
            config={"session": 2}
        )
        
        # Update session1
        for f in sample_files[:3]:
            store.update_file_status(
                session1.session_id,
                f,
                FileStatus.COMPLETED
            )
        
        # Verify session2 unaffected
        s2 = store.get_session(session2.session_id)
        assert s2.processed_count == 0
        assert all(f.status == FileStatus.PENDING for f in s2.files)
        
        # Update session2
        store.update_file_status(
            session2.session_id,
            sample_files[5],
            FileStatus.FAILED,
            error_message="Test error"
        )
        
        # Verify session1 unaffected
        s1 = store.get_session(session1.session_id)
        assert s1.failed_count == 0
        
        store.close()
    
    def test_session_survives_process_restart(self, db_path, sample_files, output_dir):
        """Session data persists across process restarts (store reconnection)."""
        # First "process"
        store1 = SQLiteSessionStore(db_path)
        session = store1.create_session(
            processor_name="test",
            file_paths=sample_files,
            config={"persistent": True}
        )
        
        for f in sample_files[:7]:
            store1.update_file_status(
                session.session_id,
                f,
                FileStatus.COMPLETED
            )
        
        session_id = session.session_id
        store1.checkpoint(session_id)
        store1.close()
        
        # Simulate "process restart" by creating new store
        store2 = SQLiteSessionStore(db_path)
        
        retrieved = store2.get_session(session_id)
        
        assert retrieved is not None
        assert retrieved.processor_name == "test"
        assert retrieved.config["persistent"] is True
        assert retrieved.processed_count == 7
        
        pending = store2.get_pending_files(session_id)
        assert len(pending) == 3
        
        store2.close()
    
    def test_clean_old_sessions_integration(self, db_path, sample_files, output_dir):
        """Test cleaning old sessions works correctly."""
        from datetime import datetime, timedelta
        
        store = SQLiteSessionStore(db_path)
        
        # Create sessions with different ages
        old_session = store.create_session(
            processor_name="old-processor",
            file_paths=sample_files[:2],
            config={}
        )
        
        new_session = store.create_session(
            processor_name="new-processor",
            file_paths=sample_files[2:],
            config={}
        )
        
        # Make old session actually old
        with store._transaction() as conn:
            old_date = (datetime.now() - timedelta(days=30)).isoformat()
            conn.execute(
                "UPDATE sessions SET created_at = ? WHERE id = ?",
                (old_date, old_session.session_id)
            )
        
        # Clean sessions older than 7 days
        deleted = store.delete_sessions_older_than(7)
        
        assert deleted == 1
        assert store.get_session(old_session.session_id) is None
        assert store.get_session(new_session.session_id) is not None
        
        store.close()
