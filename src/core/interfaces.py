"""Abstract interfaces for audio processing components."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from .types import (
    ParameterSpec,
    ProcessorCategory,
    ProcessResult,
    Session,
    FileRecord,
    FileStatus,
)


class AudioProcessor(ABC):
    """
    Abstract base class for all audio processors.
    
    Processors are PURE FUNCTIONS - they take input, produce output,
    and have no side effects beyond file I/O. Session management is
    handled by the SessionManager, not by processors.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this processor."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version string."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        pass

    @property
    @abstractmethod
    def category(self) -> ProcessorCategory:
        """Category for UI organization."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> List[ParameterSpec]:
        """List of parameters this processor accepts."""
        pass

    @abstractmethod
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        **kwargs
    ) -> ProcessResult:
        """
        Process a single audio file.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output files
            **kwargs: Processor-specific parameters
            
        Returns:
            ProcessResult with success status and output paths
        """
        pass

    def validate_params(self, **kwargs) -> List[str]:
        """
        Validate parameters before processing.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                errors.append(f"Missing required parameter: {param.name}")
            if param.name in kwargs:
                value = kwargs[param.name]
                if param.min_value is not None and value < param.min_value:
                    errors.append(
                        f"{param.name} must be >= {param.min_value}"
                    )
                if param.max_value is not None and value > param.max_value:
                    errors.append(
                        f"{param.name} must be <= {param.max_value}"
                    )
        return errors


class SessionStore(ABC):
    """
    Abstract interface for session persistence.
    
    Implementations can use SQLite, JSON files, or other storage backends.
    """

    @abstractmethod
    def create_session(
        self,
        processor_name: str,
        file_paths: List[Path],
        config: dict
    ) -> Session:
        """Create a new processing session."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""
        pass

    @abstractmethod
    def list_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Session]:
        """List sessions, optionally filtered by status."""
        pass

    @abstractmethod
    def update_file_status(
        self,
        session_id: str,
        file_path: Path,
        status: FileStatus,
        error_message: Optional[str] = None,
        output_paths: Optional[List[Path]] = None
    ) -> None:
        """Update the status of a file in a session."""
        pass

    @abstractmethod
    def checkpoint(self, session_id: str) -> None:
        """Save current session state (for crash recovery)."""
        pass

    @abstractmethod
    def complete_session(
        self,
        session_id: str,
        success: bool
    ) -> None:
        """Mark a session as completed or failed."""
        pass

    @abstractmethod
    def get_pending_files(self, session_id: str) -> List[FileRecord]:
        """Get files that haven't been processed yet."""
        pass


class ProgressReporter(ABC):
    """Abstract interface for progress reporting."""

    @abstractmethod
    def start(self, total: int, description: str = "") -> None:
        """Start progress tracking."""
        pass

    @abstractmethod
    def update(self, current: int, message: str = "") -> None:
        """Update progress."""
        pass

    @abstractmethod
    def complete(self, message: str = "") -> None:
        """Mark as complete."""
        pass

    @abstractmethod
    def error(self, message: str) -> None:
        """Report an error."""
        pass
