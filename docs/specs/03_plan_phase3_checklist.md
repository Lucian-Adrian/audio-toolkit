# Phase 3: Session Management - Implementation Checklist

> **Status:** ✅ COMPLETE  
> **Last Verified:** 2025-11-30  
> **Tests:** 289 passed (79% coverage)
> **All tests use real implementations - no data mocking to make tests pass**

---

## Overview

Phase 3 implements crash recovery and session management for batch audio processing operations. This enables users to:
- Resume interrupted batch operations
- Track processing progress persistently
- Handle Ctrl+C gracefully
- Clean up old sessions

---

## Task Checklist

### 3.1 Session Store Implementation

#### 3.1.1 Create `src/orchestration/__init__.py`
- [x] **File created:** `src/orchestration/__init__.py`
- [x] **Exports:** `SQLiteSessionStore`, `SessionManager`
- [x] **Verified:** Import works correctly

```python
# Verification
from src.orchestration import SQLiteSessionStore, SessionManager
```

#### 3.1.2 Create `src/orchestration/session_store.py` with SQLite implementation
- [x] **File created:** `src/orchestration/session_store.py` (495 lines)
- [x] **Class:** `SQLiteSessionStore(SessionStore)`
- [x] **Thread-safe:** Thread-local connections with `threading.local()`
- [x] **WAL mode:** Enabled for better concurrency
- [x] **Foreign keys:** Enabled with `PRAGMA foreign_keys=ON`

**Methods implemented:**
| Method | Status | Description |
|--------|--------|-------------|
| `__init__(db_path)` | ✅ | Initialize with configurable database path |
| `_init_db()` | ✅ | Create tables with proper schema |
| `create_session(processor_name, file_paths, config)` | ✅ | Insert session and file records |
| `get_session(session_id)` | ✅ | SELECT session with all file records |
| `get_latest_incomplete()` | ✅ | Get most recent IN_PROGRESS or PAUSED session |
| `list_sessions(status, limit)` | ✅ | List sessions with optional filtering |
| `update_file_status(session_id, file_path, status, ...)` | ✅ | Update file status and session counters |
| `checkpoint(session_id)` | ✅ | Force commit and WAL checkpoint |
| `complete_session(session_id, success)` | ✅ | Mark session COMPLETED or FAILED |
| `pause_session(session_id)` | ✅ | Mark session PAUSED, reset PROCESSING to PENDING |
| `get_pending_files(session_id)` | ✅ | Get PENDING/PROCESSING files for resume |
| `delete_session(session_id)` | ✅ | Delete session with cascade |
| `delete_sessions_older_than(days)` | ✅ | Purge old sessions |
| `close()` | ✅ | Close database connection |

**Database Schema:**
```sql
-- sessions table
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('in_progress', 'completed', 'failed', 'paused')),
    processor_name TEXT NOT NULL,
    config_json TEXT NOT NULL,
    total_files INTEGER NOT NULL DEFAULT 0,
    processed_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0
);

-- session_files table
CREATE TABLE session_files (
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
```

#### 3.1.3 Write tests (`tests/unit/test_session_store.py`)
- [x] **File created:** `tests/unit/test_session_store.py` (20 tests)
- [x] **All tests pass:** ✅

| Test | Status | Requirement |
|------|--------|-------------|
| `test_create_session` | ✅ | SESSION-001: Create session with files |
| `test_get_session` | ✅ | Retrieve session by ID |
| `test_get_session_not_found` | ✅ | Return None for non-existent |
| `test_update_file_status_completed` | ✅ | SESSION-002: Update to completed |
| `test_update_file_status_failed` | ✅ | SESSION-003: Update to failed with error |
| `test_update_file_status_processing` | ✅ | Track processing start time |
| `test_get_latest_incomplete` | ✅ | SESSION-005: Get recent incomplete |
| `test_get_latest_incomplete_none` | ✅ | Return None when all complete |
| `test_list_sessions` | ✅ | List with DESC order |
| `test_list_sessions_with_status_filter` | ✅ | Filter by status |
| `test_checkpoint` | ✅ | Commit to disk |
| `test_complete_session_success` | ✅ | Mark COMPLETED |
| `test_complete_session_failed` | ✅ | Mark FAILED |
| `test_pause_session` | ✅ | Mark PAUSED, reset PROCESSING |
| `test_get_pending_files` | ✅ | Get unprocessed files |
| `test_delete_session` | ✅ | Delete with cascade |
| `test_delete_session_not_found` | ✅ | Return False if not found |
| `test_delete_sessions_older_than` | ✅ | Purge old sessions |
| `test_session_isolation` | ✅ | Sessions don't interfere |
| `test_config_preserved` | ✅ | JSON config correctly stored |

---

### 3.2 Session Manager

#### 3.2.1 Create `src/orchestration/session.py` with `SessionManager`
- [x] **File created:** `src/orchestration/session.py` (287 lines)
- [x] **Class:** `SessionManager`
- [x] **Principle:** Only component that writes to session database

**Methods implemented:**
| Method | Status | Description |
|--------|--------|-------------|
| `__init__(store, checkpoint_interval, progress)` | ✅ | Initialize with configurable checkpoint |
| `run_batch(processor, input_files, output_dir, config, resume_session_id)` | ✅ | Main batch processing loop |
| `resume_latest()` | ✅ | Resume most recent incomplete (raises if none) |
| `get_resumable_session()` | ✅ | Get resumable session (returns None if none) |
| `list_sessions(status, limit)` | ✅ | Delegate to store |
| `clean_old_sessions(days)` | ✅ | Delete old sessions |

**Batch Processing Flow:**
1. Create or resume session
2. Register signal handlers
3. For each pending file:
   - Mark as PROCESSING
   - Call `processor.process()` (pure function)
   - Record result (COMPLETED or FAILED)
   - Checkpoint every N files
4. Mark session COMPLETED/FAILED
5. Restore signal handlers
6. Return final session state

#### 3.2.2 Implement signal handling for graceful Ctrl+C
- [x] **Implemented:** `_register_signal_handlers()`, `_restore_signal_handlers()`, `_handle_interrupt()`
- [x] **Signals handled:** SIGINT (Ctrl+C), SIGTERM
- [x] **Behavior:** Checkpoint, mark session PAUSED, show message

```python
def _handle_interrupt(self, signum, frame):
    self._interrupted = True
    if self._current_session:
        self.store.checkpoint(self._current_session.session_id)
        self.store.pause_session(self._current_session.session_id)
        # Show user message about resuming
```

#### 3.2.3 Write tests (`tests/unit/test_session_manager.py`)
- [x] **File created:** `tests/unit/test_session_manager.py` (18 tests)
- [x] **All tests pass:** ✅
- [x] **Uses real SQLite database** (not mocked)

| Test | Status | Requirement |
|------|--------|-------------|
| `test_run_batch_creates_session` | ✅ | Session created on batch start |
| `test_run_batch_updates_file_status` | ✅ | File status updated after processing |
| `test_run_batch_handles_failures` | ✅ | Failures recorded correctly |
| `test_run_batch_checkpoints` | ✅ | AC-SESSION-4: Checkpoint every N files |
| `test_resume_skips_completed` | ✅ | AC-SESSION-1: Resume skips completed files |
| `test_resume_completed_session_fails` | ✅ | AC-SESSION-5: Error on completed session |
| `test_resume_nonexistent_session_fails` | ✅ | SessionNotFoundError raised |
| `test_resume_latest` | ✅ | Gets most recent incomplete |
| `test_resume_latest_none` | ✅ | Raises if no incomplete |
| `test_get_resumable_session` | ✅ | Returns session or None |
| `test_get_resumable_session_none` | ✅ | Returns None if all complete |
| `test_list_sessions` | ✅ | Delegates to store |
| `test_clean_old_sessions` | ✅ | Purges old sessions |
| `test_session_completes_successfully` | ✅ | Status COMPLETED on success |
| `test_session_completes_with_failures` | ✅ | Partial success still completes |
| `test_session_fails_when_all_fail` | ✅ | Status FAILED when all fail |
| `test_processor_exception_handled` | ✅ | Exceptions caught and recorded |
| `test_signal_handlers_registered` | ✅ | Signal handling methods exist |

#### 3.2.4 Write integration test (`tests/integration/test_crash_recovery.py`)
- [x] **File created:** `tests/integration/test_crash_recovery.py` (6 tests)
- [x] **All tests pass:** ✅
- [x] **Tests real crash/resume scenarios**

| Test | Status | Description |
|------|--------|-------------|
| `test_crash_and_resume` | ✅ | Simulate crash at file 5/10, resume processes only 5-10 |
| `test_full_batch_with_checkpointing` | ✅ | Complete batch with regular checkpoints |
| `test_resume_preserves_config` | ✅ | Original config preserved after resume |
| `test_multiple_sessions_independence` | ✅ | Sessions don't interfere |
| `test_session_survives_process_restart` | ✅ | Data persists across store reconnection |
| `test_clean_old_sessions_integration` | ✅ | Old session cleanup works |

---

### 3.3 CLI Integration

#### 3.3.1 Create `src/presentation/cli/session_cmd.py`
- [x] **File created:** `src/presentation/cli/session_cmd.py` (430 lines)
- [x] **Registered in CLI:** `src/presentation/cli/__init__.py`

**Commands implemented:**
| Command | Status | Description |
|---------|--------|-------------|
| `sessions list` | ✅ | List recent sessions with rich table |
| `sessions info <id>` | ✅ | Show detailed session info |
| `sessions resume [id]` | ✅ | Show resume instructions |
| `sessions clean` | ✅ | Delete old sessions |
| `sessions delete <id>` | ✅ | Delete specific session |

**Options:**
- `--limit`, `-n`: Number of sessions to show
- `--status`, `-s`: Filter by status
- `--db`: Custom database path
- `--files`, `-f`: Show individual file statuses
- `--force`, `-f`: Skip confirmation
- `--dry-run`: Preview without deleting
- `--older-than`: Duration for clean (7d, 2w, 1m)

#### 3.3.2 Update split and convert commands to use SessionManager
- [x] **Updated:** `src/presentation/cli/split_cmd.py`
- [x] **Updated:** `src/presentation/cli/convert_cmd.py`

**New options added to both commands:**
| Option | Status | Description |
|--------|--------|-------------|
| `--resume` | ✅ | Resume most recent incomplete session |
| `--session <id>` | ✅ | Resume specific session by ID |

**Integration features:**
- [x] SessionManager orchestrates all file processing
- [x] Automatic session creation for new batches
- [x] Progress tracking through SessionManager
- [x] Graceful Ctrl+C handling with session pause
- [x] Session summary shown after completion

---

## Verification Commands

```bash
# Run all tests
pytest -v

# Run Phase 3 specific tests
pytest tests/unit/test_session_store.py tests/unit/test_session_manager.py tests/integration/test_crash_recovery.py -v

# Run with coverage
pytest --cov=src.orchestration --cov-report=term-missing

# Manual CLI verification
audiotoolkit sessions list
audiotoolkit sessions info <session-id>
audiotoolkit sessions clean --dry-run
audiotoolkit split fixed ./audio_folder -d 30 --dry-run
audiotoolkit convert files ./audio_folder -f mp3 --resume
```

---

## Architecture Verification

### Pure Function Pattern ✅
```python
# Processors are pure functions - NO database writes
class FixedSplitter(AudioProcessor):
    def process(self, input_path: Path, output_dir: Path, **kwargs) -> ProcessResult:
        # Read → Transform → Write → Return
        # NO session DB access here
        return ProcessResult(success=True, output_paths=[...])
```

### Session Manager Orchestration ✅
```python
# ONLY SessionManager writes to database
class SessionManager:
    def run_batch(self, processor, input_files, output_dir, config, resume_session_id=None):
        session = self.store.create_session(...)  # DB write
        for file in files:
            self.store.update_file_status(..., FileStatus.PROCESSING)  # DB write
            result = processor.process(file, output_dir, **config)  # Pure function call
            self.store.update_file_status(..., result.status)  # DB write
        self.store.complete_session(...)  # DB write
```

### Test Independence ✅
- All tests use real SQLite databases (in temp directories)
- No mocking of database operations in session tests
- CLI tests mock SessionManager to avoid side effects
- Integration tests verify full crash/resume flow

---

## Files Created/Modified

### New Files
| File | Lines | Purpose |
|------|-------|---------|
| `src/orchestration/__init__.py` | 6 | Package exports |
| `src/orchestration/session_store.py` | 495 | SQLite session persistence |
| `src/orchestration/session.py` | 287 | Batch orchestration with checkpointing |
| `src/presentation/cli/session_cmd.py` | 430 | CLI session management commands |
| `tests/unit/test_session_store.py` | 280 | SessionStore unit tests |
| `tests/unit/test_session_manager.py` | 290 | SessionManager unit tests |
| `tests/integration/test_crash_recovery.py` | 240 | Crash recovery integration tests |

### Modified Files
| File | Changes |
|------|---------|
| `src/core/interfaces.py` | Added 5 abstract methods to SessionStore |
| `src/presentation/cli/__init__.py` | Registered sessions command |
| `src/presentation/cli/split_cmd.py` | Added SessionManager integration, --resume |
| `src/presentation/cli/convert_cmd.py` | Added SessionManager integration, --resume |
| `tests/unit/test_cli_split.py` | Updated to mock SessionManager |
| `tests/unit/test_cli_convert.py` | Updated to mock SessionManager |

---

## Exit Criteria

| Criterion | Status |
|-----------|--------|
| Batch operations create sessions | ✅ |
| Ctrl+C gracefully saves state | ✅ |
| `--resume` continues from last checkpoint | ✅ |
| `sessions list` shows all sessions | ✅ |
| All 289 tests pass | ✅ |
| Coverage >= 79% | ✅ |

---

**Phase 3 Complete** ✅
