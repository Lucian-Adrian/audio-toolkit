"""SQLite-based session store for crash recovery and batch tracking."""

import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from ..core.exceptions import SessionError, SessionNotFoundError
from ..core.interfaces import SessionStore
from ..core.types import FileRecord, FileStatus, Session, SessionStatus


class SQLiteSessionStore(SessionStore):
    """
    SQLite implementation of SessionStore for persistent session tracking.
    
    Provides crash recovery by persisting session state to disk.
    Thread-safe with connection pooling per thread.
    """
    
    _DEFAULT_DB_PATH = Path("data/sessions/sessions.db")
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the session store.
        
        Args:
            db_path: Path to SQLite database file. Defaults to data/sessions/sessions.db
        """
        self.db_path = db_path or self._DEFAULT_DB_PATH
        self._local = threading.local()
        self._init_db()
    
    @property
    def _connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._local.connection = sqlite3.connect(str(self.db_path))
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys=ON")
        return self._local.connection
    
    @contextmanager
    def _transaction(self):
        """Context manager for database transactions."""
        conn = self._connection
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._transaction() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL CHECK (status IN ('in_progress', 'completed', 'failed', 'paused')),
                    processor_name TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    total_files INTEGER NOT NULL DEFAULT 0,
                    processed_count INTEGER NOT NULL DEFAULT 0,
                    failed_count INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS session_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    file_path TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'skipped')),
                    output_paths_json TEXT,
                    checksum TEXT,
                    error_message TEXT,
                    started_at TIMESTAMP,
                    processed_at TIMESTAMP,
                    UNIQUE(session_id, file_path)
                );

                CREATE INDEX IF NOT EXISTS idx_session_files_status 
                    ON session_files(session_id, status);
                CREATE INDEX IF NOT EXISTS idx_sessions_status 
                    ON sessions(status);
                CREATE INDEX IF NOT EXISTS idx_sessions_created 
                    ON sessions(created_at DESC);
            """)
    
    def _compute_checksum(self, file_path: Path) -> Optional[str]:
        """Compute MD5 checksum of a file (first 64KB for speed)."""
        try:
            hasher = hashlib.md5()
            with open(file_path, "rb") as f:
                # Read first 64KB for quick checksum
                chunk = f.read(65536)
                hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, IOError):
            return None
    
    def _session_from_row(self, row: sqlite3.Row, files: List[FileRecord]) -> Session:
        """Convert database row to Session object."""
        return Session(
            session_id=row["id"],
            processor_name=row["processor_name"],
            status=SessionStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
            config=json.loads(row["config_json"]) if row["config_json"] else {},
            total_files=row["total_files"],
            processed_count=row["processed_count"],
            failed_count=row["failed_count"],
            files=files,
        )
    
    def _file_record_from_row(self, row: sqlite3.Row) -> FileRecord:
        """Convert database row to FileRecord object."""
        output_paths_json = row["output_paths_json"]
        output_paths = json.loads(output_paths_json) if output_paths_json else []
        
        return FileRecord(
            file_path=Path(row["file_path"]),
            status=FileStatus(row["status"]),
            error_message=row["error_message"],
            output_paths=[Path(p) for p in output_paths],
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            processed_at=datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None,
        )
    
    def create_session(
        self,
        processor_name: str,
        file_paths: List[Path],
        config: dict
    ) -> Session:
        """
        Create a new processing session.
        
        Args:
            processor_name: Name of the processor being used
            file_paths: List of files to process
            config: Processor configuration parameters
            
        Returns:
            Newly created Session object
        """
        session_id = str(uuid4())
        now = datetime.now().isoformat()
        config_json = json.dumps(config)
        
        with self._transaction() as conn:
            # Insert session
            conn.execute(
                """
                INSERT INTO sessions (id, created_at, updated_at, status, processor_name, config_json, total_files)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, now, now, SessionStatus.IN_PROGRESS.value, processor_name, config_json, len(file_paths))
            )
            
            # Insert file records
            file_records = []
            for file_path in file_paths:
                checksum = self._compute_checksum(file_path)
                conn.execute(
                    """
                    INSERT INTO session_files (session_id, file_path, status, checksum)
                    VALUES (?, ?, ?, ?)
                    """,
                    (session_id, str(file_path), FileStatus.PENDING.value, checksum)
                )
                file_records.append(FileRecord(
                    file_path=file_path,
                    status=FileStatus.PENDING,
                ))
        
        return Session(
            session_id=session_id,
            processor_name=processor_name,
            status=SessionStatus.IN_PROGRESS,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            config=config,
            total_files=len(file_paths),
            files=file_records,
        )
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session object or None if not found
        """
        conn = self._connection
        
        # Get session
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,)
        ).fetchone()
        
        if not row:
            return None
        
        # Get file records
        file_rows = conn.execute(
            "SELECT * FROM session_files WHERE session_id = ? ORDER BY id",
            (session_id,)
        ).fetchall()
        
        files = [self._file_record_from_row(fr) for fr in file_rows]
        return self._session_from_row(row, files)
    
    def get_latest_incomplete(self) -> Optional[Session]:
        """
        Get the most recent incomplete session.
        
        Returns:
            Most recent session with status IN_PROGRESS or PAUSED, or None
        """
        conn = self._connection
        
        row = conn.execute(
            """
            SELECT * FROM sessions 
            WHERE status IN (?, ?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (SessionStatus.IN_PROGRESS.value, SessionStatus.PAUSED.value)
        ).fetchone()
        
        if not row:
            return None
        
        return self.get_session(row["id"])
    
    def list_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Session]:
        """
        List sessions, optionally filtered by status.
        
        Args:
            status: Filter by status (optional)
            limit: Maximum number of sessions to return
            
        Returns:
            List of Session objects
        """
        conn = self._connection
        
        if status:
            rows = conn.execute(
                """
                SELECT * FROM sessions 
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (status, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM sessions 
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
        
        sessions = []
        for row in rows:
            # Get file records for each session
            file_rows = conn.execute(
                "SELECT * FROM session_files WHERE session_id = ? ORDER BY id",
                (row["id"],)
            ).fetchall()
            files = [self._file_record_from_row(fr) for fr in file_rows]
            sessions.append(self._session_from_row(row, files))
        
        return sessions
    
    def update_file_status(
        self,
        session_id: str,
        file_path: Path,
        status: FileStatus,
        error_message: Optional[str] = None,
        output_paths: Optional[List[Path]] = None
    ) -> None:
        """
        Update the status of a file in a session.
        
        Args:
            session_id: Session identifier
            file_path: Path to the file being updated
            status: New status for the file
            error_message: Error message if status is FAILED
            output_paths: Output file paths if status is COMPLETED
        """
        now = datetime.now().isoformat()
        output_paths_json = json.dumps([str(p) for p in output_paths]) if output_paths else None
        
        with self._transaction() as conn:
            # Update file record
            if status == FileStatus.PROCESSING:
                conn.execute(
                    """
                    UPDATE session_files 
                    SET status = ?, started_at = ?
                    WHERE session_id = ? AND file_path = ?
                    """,
                    (status.value, now, session_id, str(file_path))
                )
            else:
                conn.execute(
                    """
                    UPDATE session_files 
                    SET status = ?, error_message = ?, output_paths_json = ?, processed_at = ?
                    WHERE session_id = ? AND file_path = ?
                    """,
                    (status.value, error_message, output_paths_json, now, session_id, str(file_path))
                )
            
            # Update session counters
            if status == FileStatus.COMPLETED:
                conn.execute(
                    """
                    UPDATE sessions 
                    SET processed_count = processed_count + 1, updated_at = ?
                    WHERE id = ?
                    """,
                    (now, session_id)
                )
            elif status == FileStatus.FAILED:
                conn.execute(
                    """
                    UPDATE sessions 
                    SET failed_count = failed_count + 1, updated_at = ?
                    WHERE id = ?
                    """,
                    (now, session_id)
                )
            elif status == FileStatus.SKIPPED:
                conn.execute(
                    """
                    UPDATE sessions 
                    SET processed_count = processed_count + 1, updated_at = ?
                    WHERE id = ?
                    """,
                    (now, session_id)
                )
    
    def checkpoint(self, session_id: str) -> None:
        """
        Force a checkpoint (commit to disk).

        Args:
            session_id: Session identifier
        """
        now = datetime.now().isoformat()
        with self._transaction() as conn:
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id)
            )
        # Force WAL checkpoint outside transaction
        self._connection.execute("PRAGMA wal_checkpoint(PASSIVE)")

    def complete_session(
        self,
        session_id: str,
        success: bool
    ) -> None:
        """
        Mark a session as completed or failed.
        
        Args:
            session_id: Session identifier
            success: True if completed successfully, False if failed
        """
        status = SessionStatus.COMPLETED if success else SessionStatus.FAILED
        now = datetime.now().isoformat()
        
        with self._transaction() as conn:
            conn.execute(
                "UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, now, session_id)
            )
    
    def pause_session(self, session_id: str) -> None:
        """
        Mark a session as paused (for graceful Ctrl+C handling).
        
        Args:
            session_id: Session identifier
        """
        now = datetime.now().isoformat()
        
        with self._transaction() as conn:
            # Mark any PROCESSING files as PENDING for resume
            conn.execute(
                """
                UPDATE session_files 
                SET status = ?
                WHERE session_id = ? AND status = ?
                """,
                (FileStatus.PENDING.value, session_id, FileStatus.PROCESSING.value)
            )
            
            conn.execute(
                "UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?",
                (SessionStatus.PAUSED.value, now, session_id)
            )
    
    def get_pending_files(self, session_id: str) -> List[FileRecord]:
        """
        Get files that haven't been processed yet.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of FileRecord objects with PENDING or PROCESSING status
        """
        conn = self._connection
        
        rows = conn.execute(
            """
            SELECT * FROM session_files 
            WHERE session_id = ? AND status IN (?, ?)
            ORDER BY id
            """,
            (session_id, FileStatus.PENDING.value, FileStatus.PROCESSING.value)
        ).fetchall()
        
        return [self._file_record_from_row(row) for row in rows]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its file records.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        with self._transaction() as conn:
            # Foreign key ON DELETE CASCADE handles session_files
            cursor = conn.execute(
                "DELETE FROM sessions WHERE id = ?",
                (session_id,)
            )
            return cursor.rowcount > 0
    
    def delete_sessions_older_than(self, days: int) -> int:
        """
        Purge old sessions.
        
        Args:
            days: Delete sessions older than this many days
            
        Returns:
            Number of sessions deleted
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._transaction() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE created_at < ?",
                (cutoff,)
            )
            return cursor.rowcount
    
    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
