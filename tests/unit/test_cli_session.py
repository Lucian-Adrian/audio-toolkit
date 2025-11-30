"""Tests for session CLI commands."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from src.presentation.cli.session_cmd import app, _format_duration, _status_style, _file_status_style
from src.core.types import Session, SessionStatus, FileStatus, FileRecord


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_format_duration_seconds(self):
        """Test formatting duration in seconds."""
        start = datetime.now() - timedelta(seconds=45)
        end = datetime.now()
        result = _format_duration(start, end)
        assert "s" in result
        assert int(result.replace("s", "")) >= 44  # Allow for minor timing differences
    
    def test_format_duration_minutes(self):
        """Test formatting duration in minutes."""
        start = datetime.now() - timedelta(minutes=5, seconds=30)
        end = datetime.now()
        result = _format_duration(start, end)
        assert "m" in result
        assert "5m" in result
    
    def test_format_duration_hours(self):
        """Test formatting duration in hours."""
        start = datetime.now() - timedelta(hours=2, minutes=30)
        end = datetime.now()
        result = _format_duration(start, end)
        assert "h" in result
        assert "2h" in result
    
    def test_format_duration_default_end(self):
        """Test formatting duration with default end time."""
        start = datetime.now() - timedelta(seconds=10)
        result = _format_duration(start)  # No end time, uses now
        assert "s" in result
    
    def test_status_style_in_progress(self):
        """Test style for in_progress status."""
        result = _status_style(SessionStatus.IN_PROGRESS)
        assert "yellow" in result
        assert "in_progress" in result
    
    def test_status_style_completed(self):
        """Test style for completed status."""
        result = _status_style(SessionStatus.COMPLETED)
        assert "green" in result
        assert "completed" in result
    
    def test_status_style_failed(self):
        """Test style for failed status."""
        result = _status_style(SessionStatus.FAILED)
        assert "red" in result
        assert "failed" in result
    
    def test_status_style_paused(self):
        """Test style for paused status."""
        result = _status_style(SessionStatus.PAUSED)
        assert "cyan" in result
        assert "paused" in result
    
    def test_file_status_style_pending(self):
        """Test style for pending file status."""
        result = _file_status_style(FileStatus.PENDING)
        assert "dim" in result
        assert "pending" in result
    
    def test_file_status_style_completed(self):
        """Test style for completed file status."""
        result = _file_status_style(FileStatus.COMPLETED)
        assert "green" in result
        assert "completed" in result
    
    def test_file_status_style_failed(self):
        """Test style for failed file status."""
        result = _file_status_style(FileStatus.FAILED)
        assert "red" in result
        assert "failed" in result


class TestListSessions:
    """Tests for list sessions command."""
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_list_sessions_empty(self, mock_store_class, runner):
        """Test listing sessions when none exist."""
        mock_store = Mock()
        mock_store.list_sessions.return_value = []
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        assert "No sessions found" in result.output
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_list_sessions_with_results(self, mock_store_class, runner):
        """Test listing sessions with results."""
        mock_session = Session(
            session_id="test-session-12345",
            processor_name="test-processor",
            status=SessionStatus.COMPLETED,
            total_files=10,
            processed_count=10,
            failed_count=0,
            created_at=datetime.now() - timedelta(hours=1),
            updated_at=datetime.now(),
        )
        
        mock_store = MagicMock()
        mock_store.list_sessions.return_value = [mock_session]
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        # Just check that something related to sessions is shown
        assert "Recent Sessions" in result.output or "test" in result.output
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_list_sessions_with_limit(self, mock_store_class, runner):
        """Test listing sessions with limit option."""
        mock_store = Mock()
        mock_store.list_sessions.return_value = []
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["list", "--limit", "5"])
        
        mock_store.list_sessions.assert_called_once_with(status=None, limit=5)
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_list_sessions_with_status_filter(self, mock_store_class, runner):
        """Test listing sessions with status filter."""
        mock_store = Mock()
        mock_store.list_sessions.return_value = []
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["list", "--status", "completed"])
        
        mock_store.list_sessions.assert_called_once_with(status="completed", limit=10)
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_list_sessions_shows_resumable_hint(self, mock_store_class, runner):
        """Test that resumable sessions show a hint."""
        mock_session = Session(
            session_id="test-session-12345",
            processor_name="test-processor",
            status=SessionStatus.IN_PROGRESS,  # Resumable
            total_files=10,
            processed_count=5,
            failed_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        mock_store = Mock()
        mock_store.list_sessions.return_value = [mock_session]
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["list"])
        
        assert "can be resumed" in result.output


class TestSessionInfo:
    """Tests for session info command."""
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_info_not_found(self, mock_store_class, runner):
        """Test info for non-existent session."""
        mock_store = Mock()
        mock_store.list_sessions.return_value = []
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["info", "nonexistent"])
        
        assert result.exit_code == 1
        assert "No session found" in result.output
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_info_multiple_matches(self, mock_store_class, runner):
        """Test info when multiple sessions match."""
        sessions = [
            Session(
                session_id="test-session-111",
                processor_name="proc1",
                status=SessionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Session(
                session_id="test-session-222",
                processor_name="proc2",
                status=SessionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]
        
        mock_store = Mock()
        mock_store.list_sessions.return_value = sessions
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["info", "test"])  # Matches both
        
        assert result.exit_code == 1
        assert "Multiple sessions match" in result.output
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_info_success(self, mock_store_class, runner):
        """Test info for existing session."""
        mock_session = Session(
            session_id="test-session-12345",
            processor_name="test-processor",
            status=SessionStatus.COMPLETED,
            total_files=10,
            processed_count=10,
            failed_count=0,
            created_at=datetime.now() - timedelta(hours=1),
            updated_at=datetime.now(),
            config={"param1": "value1"},
        )
        
        mock_store = Mock()
        mock_store.list_sessions.return_value = [mock_session]
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["info", "test-session"])
        
        assert result.exit_code == 0
        assert "test-session-12345" in result.output
        assert "test-processor" in result.output
        assert "param1" in result.output
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_info_with_files(self, mock_store_class, runner):
        """Test info with --files flag."""
        file_record = FileRecord(
            file_path=Path("/path/to/file.mp3"),
            status=FileStatus.COMPLETED,
        )
        mock_session = Session(
            session_id="test-session-12345",
            processor_name="test-processor",
            status=SessionStatus.COMPLETED,
            total_files=1,
            processed_count=1,
            failed_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            files=[file_record],
        )
        
        mock_store = Mock()
        mock_store.list_sessions.return_value = [mock_session]
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["info", "test-session", "--files"])
        
        assert result.exit_code == 0
        assert "file.mp3" in result.output


class TestResumeSession:
    """Tests for resume session command."""
    
    @patch("src.presentation.cli.session_cmd.SessionManager")
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_resume_no_incomplete_sessions(self, mock_store_class, mock_manager_class, runner):
        """Test resume when no incomplete sessions exist."""
        mock_store = Mock()
        mock_manager = Mock()
        mock_manager.get_resumable_session.return_value = None
        mock_store_class.return_value = mock_store
        mock_manager_class.return_value = mock_manager
        
        result = runner.invoke(app, ["resume"])
        
        assert result.exit_code == 0
        assert "No incomplete sessions" in result.output
    
    @patch("src.presentation.cli.session_cmd.SessionManager")
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_resume_already_completed(self, mock_store_class, mock_manager_class, runner):
        """Test resume for already completed session."""
        mock_session = Session(
            session_id="test-session-12345",
            processor_name="test-processor",
            status=SessionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        mock_store = Mock()
        mock_store.list_sessions.return_value = [mock_session]
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["resume", "test"])
        
        assert result.exit_code == 1
        assert "already completed" in result.output
    
    @patch("src.presentation.cli.session_cmd.SessionManager")
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_resume_active_session_without_force(self, mock_store_class, mock_manager_class, runner):
        """Test resume for active session without --force."""
        mock_session = Session(
            session_id="test-session-12345",
            processor_name="test-processor",
            status=SessionStatus.IN_PROGRESS,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        mock_store = Mock()
        mock_store.list_sessions.return_value = [mock_session]
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["resume", "test"])
        
        assert result.exit_code == 1
        assert "appears to be active" in result.output
    
    @patch("src.presentation.cli.session_cmd.SessionManager")
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_resume_with_force(self, mock_store_class, mock_manager_class, runner):
        """Test resume for active session with --force."""
        mock_session = Session(
            session_id="test-session-12345",
            processor_name="test-processor",
            status=SessionStatus.IN_PROGRESS,
            total_files=10,
            processed_count=5,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        mock_store = Mock()
        mock_store.list_sessions.return_value = [mock_session]
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["resume", "test", "--force"])
        
        assert result.exit_code == 0
        assert "Resuming session" in result.output


class TestCleanSessions:
    """Tests for clean sessions command."""
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_clean_invalid_duration(self, mock_store_class, runner):
        """Test clean with invalid duration format (no d/w/m suffix)."""
        mock_store = MagicMock()
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["clean", "--older-than", "7x"])  # invalid suffix
        
        assert result.exit_code == 1
        assert "Invalid duration format" in result.output
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_clean_dry_run(self, mock_store_class, runner):
        """Test clean with --dry-run."""
        old_session = Session(
            session_id="old-session",
            processor_name="test",
            status=SessionStatus.COMPLETED,
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now() - timedelta(days=30),
        )
        
        mock_store = Mock()
        mock_store.list_sessions.return_value = [old_session]
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["clean", "--older-than", "7d", "--dry-run"])
        
        assert result.exit_code == 0
        assert "Would delete" in result.output
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_clean_execute(self, mock_store_class, runner):
        """Test clean execution."""
        mock_store = Mock()
        mock_store.delete_sessions_older_than.return_value = 5
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["clean", "--older-than", "7d"])
        
        assert result.exit_code == 0
        assert "Deleted 5 session(s)" in result.output
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_clean_weeks_format(self, mock_store_class, runner):
        """Test clean with weeks format."""
        mock_store = Mock()
        mock_store.delete_sessions_older_than.return_value = 2
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["clean", "--older-than", "2w"])
        
        mock_store.delete_sessions_older_than.assert_called_once_with(14)
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_clean_months_format(self, mock_store_class, runner):
        """Test clean with months format."""
        mock_store = Mock()
        mock_store.delete_sessions_older_than.return_value = 1
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["clean", "--older-than", "1m"])
        
        mock_store.delete_sessions_older_than.assert_called_once_with(30)


class TestDeleteSession:
    """Tests for delete session command."""
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_delete_not_found(self, mock_store_class, runner):
        """Test delete for non-existent session."""
        mock_store = Mock()
        mock_store.list_sessions.return_value = []
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["delete", "nonexistent", "--force"])
        
        assert result.exit_code == 1
        assert "No session found" in result.output
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_delete_with_force(self, mock_store_class, runner):
        """Test delete with --force flag."""
        mock_session = Session(
            session_id="test-session-12345",
            processor_name="test-processor",
            status=SessionStatus.COMPLETED,
            total_files=10,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        mock_store = Mock()
        mock_store.list_sessions.return_value = [mock_session]
        mock_store.delete_session.return_value = True
        mock_store_class.return_value = mock_store
        
        result = runner.invoke(app, ["delete", "test", "--force"])
        
        assert result.exit_code == 0
        assert "Deleted session" in result.output
    
    @patch("src.presentation.cli.session_cmd.SQLiteSessionStore")
    def test_delete_cancelled(self, mock_store_class, runner):
        """Test delete cancelled by user."""
        mock_session = Session(
            session_id="test-session-12345",
            processor_name="test-processor",
            status=SessionStatus.COMPLETED,
            total_files=10,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        mock_store = Mock()
        mock_store.list_sessions.return_value = [mock_session]
        mock_store_class.return_value = mock_store
        
        # User says 'n' to cancel
        result = runner.invoke(app, ["delete", "test"], input="n\n")
        
        assert result.exit_code == 0
        assert "Cancelled" in result.output


class TestCallback:
    """Tests for the callback function."""
    
    def test_callback_help(self, runner):
        """Test that callback provides help text."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Manage processing sessions" in result.output
