"""Tests for SQLiteSessionStore."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from src.orchestration.session_store import SQLiteSessionStore
from src.core.types import FileStatus, SessionStatus


class TestSQLiteSessionStore:
    """Tests for SQLiteSessionStore implementation."""
    
    @pytest.fixture
    def store(self, temp_dir):
        """Create a test session store."""
        db_path = temp_dir / "test_sessions.db"
        store = SQLiteSessionStore(db_path)
        yield store
        store.close()
    
    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample test files."""
        files = []
        for i in range(5):
            f = temp_dir / f"audio_{i}.wav"
            f.write_bytes(b"fake audio data")
            files.append(f)
        return files
    
    def test_create_session(self, store, sample_files):
        """SESSION-001: Create session with files."""
        session = store.create_session(
            processor_name="splitter-fixed",
            file_paths=sample_files,
            config={"duration_ms": 30000}
        )
        
        assert session.session_id is not None
        assert session.processor_name == "splitter-fixed"
        assert session.status == SessionStatus.IN_PROGRESS
        assert session.total_files == 5
        assert session.processed_count == 0
        assert session.failed_count == 0
        assert len(session.files) == 5
        assert all(f.status == FileStatus.PENDING for f in session.files)
    
    def test_get_session(self, store, sample_files):
        """Retrieve a session by ID."""
        created = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={"format": "mp3"}
        )
        
        retrieved = store.get_session(created.session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == created.session_id
        assert retrieved.processor_name == created.processor_name
        assert len(retrieved.files) == len(sample_files)
    
    def test_get_session_not_found(self, store):
        """Return None for non-existent session."""
        result = store.get_session("non-existent-id")
        assert result is None
    
    def test_update_file_status_completed(self, store, sample_files):
        """SESSION-002: Update file to completed."""
        session = store.create_session(
            processor_name="splitter-fixed",
            file_paths=sample_files,
            config={}
        )
        
        output_paths = [Path("output/segment_1.mp3"), Path("output/segment_2.mp3")]
        store.update_file_status(
            session.session_id,
            sample_files[0],
            FileStatus.COMPLETED,
            output_paths=output_paths
        )
        
        updated = store.get_session(session.session_id)
        file_record = next(f for f in updated.files if f.file_path == sample_files[0])
        
        assert file_record.status == FileStatus.COMPLETED
        assert len(file_record.output_paths) == 2
        assert updated.processed_count == 1
    
    def test_update_file_status_failed(self, store, sample_files):
        """SESSION-003: Update file to failed with error."""
        session = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={}
        )
        
        store.update_file_status(
            session.session_id,
            sample_files[0],
            FileStatus.FAILED,
            error_message="Corrupted file"
        )
        
        updated = store.get_session(session.session_id)
        file_record = next(f for f in updated.files if f.file_path == sample_files[0])
        
        assert file_record.status == FileStatus.FAILED
        assert file_record.error_message == "Corrupted file"
        assert updated.failed_count == 1
    
    def test_update_file_status_processing(self, store, sample_files):
        """Update file to processing status."""
        session = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={}
        )
        
        store.update_file_status(
            session.session_id,
            sample_files[0],
            FileStatus.PROCESSING
        )
        
        updated = store.get_session(session.session_id)
        file_record = next(f for f in updated.files if f.file_path == sample_files[0])
        
        assert file_record.status == FileStatus.PROCESSING
        assert file_record.started_at is not None
    
    def test_get_latest_incomplete(self, store, sample_files):
        """SESSION-005: Get most recent incomplete session."""
        # Create completed session
        session1 = store.create_session(
            processor_name="converter",
            file_paths=sample_files[:2],
            config={}
        )
        store.complete_session(session1.session_id, success=True)
        
        # Create incomplete session
        session2 = store.create_session(
            processor_name="splitter-fixed",
            file_paths=sample_files[2:],
            config={}
        )
        
        latest = store.get_latest_incomplete()
        
        assert latest is not None
        assert latest.session_id == session2.session_id
    
    def test_get_latest_incomplete_none(self, store, sample_files):
        """Return None when no incomplete sessions exist."""
        session = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={}
        )
        store.complete_session(session.session_id, success=True)
        
        latest = store.get_latest_incomplete()
        assert latest is None
    
    def test_list_sessions(self, store, sample_files):
        """List recent sessions."""
        # Create multiple sessions
        for i in range(3):
            store.create_session(
                processor_name=f"processor-{i}",
                file_paths=sample_files,
                config={}
            )
        
        sessions = store.list_sessions(limit=10)
        
        assert len(sessions) == 3
        # Should be ordered by created_at DESC
        assert sessions[0].processor_name == "processor-2"
    
    def test_list_sessions_with_status_filter(self, store, sample_files):
        """List sessions filtered by status."""
        session1 = store.create_session(
            processor_name="processor-1",
            file_paths=sample_files,
            config={}
        )
        store.complete_session(session1.session_id, success=True)
        
        session2 = store.create_session(
            processor_name="processor-2",
            file_paths=sample_files,
            config={}
        )
        
        completed = store.list_sessions(status="completed")
        in_progress = store.list_sessions(status="in_progress")
        
        assert len(completed) == 1
        assert completed[0].processor_name == "processor-1"
        assert len(in_progress) == 1
        assert in_progress[0].processor_name == "processor-2"
    
    def test_checkpoint(self, store, sample_files):
        """Checkpoint commits to disk."""
        session = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={}
        )
        
        # Update a file
        store.update_file_status(
            session.session_id,
            sample_files[0],
            FileStatus.COMPLETED
        )
        
        # Checkpoint
        store.checkpoint(session.session_id)
        
        # Verify data persisted
        updated = store.get_session(session.session_id)
        assert updated.processed_count == 1
    
    def test_complete_session_success(self, store, sample_files):
        """Mark session as completed."""
        session = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={}
        )
        
        store.complete_session(session.session_id, success=True)
        
        updated = store.get_session(session.session_id)
        assert updated.status == SessionStatus.COMPLETED
    
    def test_complete_session_failed(self, store, sample_files):
        """Mark session as failed."""
        session = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={}
        )
        
        store.complete_session(session.session_id, success=False)
        
        updated = store.get_session(session.session_id)
        assert updated.status == SessionStatus.FAILED
    
    def test_pause_session(self, store, sample_files):
        """Pause session for graceful interrupt."""
        session = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={}
        )
        
        # Mark one file as processing
        store.update_file_status(
            session.session_id,
            sample_files[0],
            FileStatus.PROCESSING
        )
        
        # Pause
        store.pause_session(session.session_id)
        
        updated = store.get_session(session.session_id)
        assert updated.status == SessionStatus.PAUSED
        
        # Processing file should be reset to pending
        file_record = next(f for f in updated.files if f.file_path == sample_files[0])
        assert file_record.status == FileStatus.PENDING
    
    def test_get_pending_files(self, store, sample_files):
        """Get files that haven't been processed."""
        session = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={}
        )
        
        # Complete some files
        store.update_file_status(
            session.session_id,
            sample_files[0],
            FileStatus.COMPLETED
        )
        store.update_file_status(
            session.session_id,
            sample_files[1],
            FileStatus.FAILED,
            error_message="Error"
        )
        
        pending = store.get_pending_files(session.session_id)
        
        assert len(pending) == 3
        assert all(f.status == FileStatus.PENDING for f in pending)
    
    def test_delete_session(self, store, sample_files):
        """Delete a specific session."""
        session = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={}
        )
        
        result = store.delete_session(session.session_id)
        
        assert result is True
        assert store.get_session(session.session_id) is None
    
    def test_delete_session_not_found(self, store):
        """Delete non-existent session returns False."""
        result = store.delete_session("non-existent-id")
        assert result is False
    
    def test_delete_sessions_older_than(self, store, sample_files):
        """Purge old sessions."""
        # Create a session
        session = store.create_session(
            processor_name="converter",
            file_paths=sample_files,
            config={}
        )
        
        # Manually make it old by updating timestamp
        with store._transaction() as conn:
            old_date = (datetime.now() - timedelta(days=10)).isoformat()
            conn.execute(
                "UPDATE sessions SET created_at = ? WHERE id = ?",
                (old_date, session.session_id)
            )
        
        deleted = store.delete_sessions_older_than(7)
        
        assert deleted == 1
        assert store.get_session(session.session_id) is None
    
    def test_session_isolation(self, store, sample_files):
        """Verify sessions don't interfere with each other."""
        session1 = store.create_session(
            processor_name="converter",
            file_paths=sample_files[:2],
            config={}
        )
        session2 = store.create_session(
            processor_name="splitter",
            file_paths=sample_files[2:],
            config={}
        )
        
        # Update file in session1
        store.update_file_status(
            session1.session_id,
            sample_files[0],
            FileStatus.COMPLETED
        )
        
        # Verify session2 unaffected
        s2 = store.get_session(session2.session_id)
        assert s2.processed_count == 0
        assert all(f.status == FileStatus.PENDING for f in s2.files)
    
    def test_config_preserved(self, store, sample_files):
        """Session config is correctly stored and retrieved."""
        config = {
            "duration_ms": 30000,
            "format": "mp3",
            "nested": {"key": "value"}
        }
        
        session = store.create_session(
            processor_name="splitter-fixed",
            file_paths=sample_files,
            config=config
        )
        
        retrieved = store.get_session(session.session_id)
        
        assert retrieved.config == config
        assert retrieved.config["nested"]["key"] == "value"
