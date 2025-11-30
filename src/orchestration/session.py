"""Session manager for orchestrating batch processing with crash recovery."""

import signal
import sys
from pathlib import Path
from typing import Callable, List, Optional

from ..core.exceptions import SessionError, SessionNotFoundError
from ..core.interfaces import AudioProcessor, ProgressReporter, SessionStore
from ..core.types import FileRecord, FileStatus, Session, SessionStatus
from ..utils.progress import RichProgressReporter, SilentProgressReporter


class SessionManager:
    """
    Orchestrates batch processing with checkpointing and crash recovery.
    
    This is the ONLY component that writes to the session database.
    Processors are pure functions - they return ProcessResult,
    and SessionManager records the result.
    
    Features:
    - Automatic session creation and tracking
    - Periodic checkpointing (every N files)
    - Graceful interrupt handling (Ctrl+C)
    - Resume from last checkpoint
    - Progress reporting
    """
    
    def __init__(
        self,
        store: SessionStore,
        checkpoint_interval: int = 100,
        progress: Optional[ProgressReporter] = None
    ):
        """
        Initialize the session manager.
        
        Args:
            store: Session store for persistence
            checkpoint_interval: Number of files between checkpoints
            progress: Progress reporter for UI updates
        """
        self.store = store
        self.checkpoint_interval = checkpoint_interval
        self.progress = progress
        self._current_session: Optional[Session] = None
        self._interrupted = False
        self._original_sigint = None
        self._original_sigterm = None
    
    def _register_signal_handlers(self) -> None:
        """Register handlers for graceful interrupt handling."""
        self._original_sigint = signal.getsignal(signal.SIGINT)
        self._original_sigterm = signal.getsignal(signal.SIGTERM)
        
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def _restore_signal_handlers(self) -> None:
        """Restore original signal handlers."""
        if self._original_sigint is not None:
            signal.signal(signal.SIGINT, self._original_sigint)
        if self._original_sigterm is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm)
    
    def _handle_interrupt(self, signum, frame) -> None:
        """
        Handle Ctrl+C and SIGTERM gracefully.
        
        Marks the current session as paused and checkpoints.
        """
        self._interrupted = True
        
        if self._current_session:
            # Checkpoint and pause
            self.store.checkpoint(self._current_session.session_id)
            self.store.pause_session(self._current_session.session_id)
            
            if self.progress:
                self.progress.error(
                    f"Interrupted! Session {self._current_session.session_id[:8]}... paused. "
                    f"Use 'audiotoolkit sessions resume' to continue."
                )
        
        # Restore original handler and re-raise
        self._restore_signal_handlers()
        
        # If original handler exists and is callable, call it
        if callable(self._original_sigint):
            self._original_sigint(signum, frame)
        else:
            # Default behavior: exit
            sys.exit(130)  # 128 + SIGINT (2)
    
    def run_batch(
        self,
        processor: AudioProcessor,
        input_files: List[Path],
        output_dir: Path,
        config: dict,
        resume_session_id: Optional[str] = None
    ) -> Session:
        """
        Execute processor on all files with checkpointing.
        
        If resume_session_id is provided, continues from last checkpoint.
        Creates a new session otherwise.
        
        Args:
            processor: Audio processor to execute
            input_files: List of input file paths
            output_dir: Directory for output files
            config: Processor configuration
            resume_session_id: Session ID to resume (optional)
            
        Returns:
            Final session state
            
        Raises:
            SessionNotFoundError: If resume_session_id not found
            SessionError: If trying to resume a completed session
        """
        self._interrupted = False
        self._register_signal_handlers()
        
        try:
            if resume_session_id:
                session = self.store.get_session(resume_session_id)
                if session is None:
                    raise SessionNotFoundError(f"Session not found: {resume_session_id}")
                
                if session.status == SessionStatus.COMPLETED:
                    raise SessionError(
                        f"Cannot resume completed session {resume_session_id}. "
                        "Start a new session instead."
                    )
                
                # Get pending files
                pending_files = self.store.get_pending_files(session.session_id)
                files_to_process = [f.file_path for f in pending_files]
                
                # Calculate already processed
                already_processed = session.total_files - len(files_to_process)
                
            else:
                session = self.store.create_session(
                    processor_name=processor.name,
                    file_paths=input_files,
                    config=config
                )
                files_to_process = input_files
                already_processed = 0
            
            self._current_session = session
            
            # Setup progress reporter
            progress = self.progress or RichProgressReporter()
            total_files = len(files_to_process)
            
            if already_processed > 0:
                description = f"Resuming {processor.name} (skipped {already_processed} completed)"
            else:
                description = f"Processing with {processor.name}"
            
            progress.start(total=total_files, description=description)
            
            processed_in_batch = 0
            
            for file_path in files_to_process:
                if self._interrupted:
                    break
                
                # Mark as processing
                self.store.update_file_status(
                    session.session_id,
                    file_path,
                    FileStatus.PROCESSING
                )
                
                try:
                    result = processor.process(file_path, output_dir, **config)
                    
                    if result.success:
                        self.store.update_file_status(
                            session.session_id,
                            file_path,
                            FileStatus.COMPLETED,
                            output_paths=result.output_paths
                        )
                    else:
                        self.store.update_file_status(
                            session.session_id,
                            file_path,
                            FileStatus.FAILED,
                            error_message=result.error_message
                        )
                        
                except Exception as e:
                    self.store.update_file_status(
                        session.session_id,
                        file_path,
                        FileStatus.FAILED,
                        error_message=str(e)
                    )
                
                processed_in_batch += 1
                progress.update(processed_in_batch)
                
                # Checkpoint every N files
                if processed_in_batch % self.checkpoint_interval == 0:
                    self.store.checkpoint(session.session_id)
            
            # Final state
            if not self._interrupted:
                # Determine final status based on results
                final_session = self.store.get_session(session.session_id)
                if final_session and final_session.failed_count == 0:
                    self.store.complete_session(session.session_id, success=True)
                elif final_session and final_session.failed_count == final_session.total_files:
                    self.store.complete_session(session.session_id, success=False)
                else:
                    # Partial success
                    self.store.complete_session(session.session_id, success=True)
                
                progress.complete(f"Processed {processed_in_batch} files")
            
            self._current_session = None
            return self.store.get_session(session.session_id)
            
        finally:
            self._restore_signal_handlers()
    
    def resume_latest(self) -> Optional[Session]:
        """
        Resume the most recent incomplete session.
        
        Returns:
            Resumed session or None if no incomplete session found
            
        Raises:
            SessionNotFoundError: If no incomplete session exists
        """
        session = self.store.get_latest_incomplete()
        
        if session is None:
            raise SessionNotFoundError("No incomplete session found to resume")
        
        return session
    
    def get_resumable_session(self) -> Optional[Session]:
        """
        Get the most recent incomplete session without raising.
        
        Returns:
            Latest incomplete session or None
        """
        return self.store.get_latest_incomplete()
    
    def list_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Session]:
        """
        List recent sessions.
        
        Args:
            status: Filter by status (optional)
            limit: Maximum number to return
            
        Returns:
            List of sessions
        """
        return self.store.list_sessions(status=status, limit=limit)
    
    def clean_old_sessions(self, days: int = 7) -> int:
        """
        Delete sessions older than specified days.
        
        Args:
            days: Delete sessions older than this
            
        Returns:
            Number of sessions deleted
        """
        return self.store.delete_sessions_older_than(days)
