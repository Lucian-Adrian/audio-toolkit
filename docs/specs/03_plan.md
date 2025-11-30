# Master Implementation Plan

> **Document Version:** 1.0.0  
> **Last Updated:** 2025-11-30  
> **Status:** Active Development

---

## Guiding Principles

### Pure Function Architecture
**Critical Constraint:** All Processor classes MUST be pure functions.

```python
# ✅ CORRECT: Pure function pattern
class FixedSplitter(AudioProcessor):
    def process(self, input_path: Path, output_dir: Path, **kwargs) -> ProcessResult:
        # Read input → Transform → Write output → Return result
        # NEVER write to session DB, NEVER mutate global state
        return ProcessResult(success=True, output_paths=[...])

# ❌ WRONG: Impure function with side effects
class BadSplitter(AudioProcessor):
    def process(self, input_path: Path, output_dir: Path, **kwargs) -> ProcessResult:
        self.session_db.update(...)  # FORBIDDEN: DB write in processor
        return ProcessResult(...)
```

**Rationale:**
- Processors are testable in isolation (no DB mocking required)
- Session Manager orchestrates DB writes based on ProcessResult
- Enables parallel processing without race conditions
- Simplifies debugging (input → output, nothing else)

---

## Phase Overview

| Phase | Name | Duration | Dependencies | Deliverable |
|-------|------|----------|--------------|-------------|
| **0** | Project Setup | 1 day | None | Runnable skeleton with `--help` |
| **1** | Foundation | 3 days | Phase 0 | Core interfaces, utils, logging |
| **2** | MVP Processors | 5 days | Phase 1 | Splitter + Converter working via CLI |
| **3** | Session Management | 4 days | Phase 2 | Crash recovery, resume capability |
| **4** | Pipeline Engine | 3 days | Phase 3 | YAML pipeline execution |
| **5** | Interactive Wizard | 3 days | Phase 4 | TUI with presets |
| **6** | Plugin System | 2 days | Phase 4 | Third-party plugin loading |
| **7** | Advanced Processors | 5 days | Phase 3 | Analysis, Voice, Transcriber |
| **8** | Polish & Release | 2 days | All | Documentation, PyPI package |

**Total Estimated Duration:** ~28 days (4 weeks)

---

## Phase 3: Session Management (Crash Recovery)

**Goal:** Implement session tracking so batch operations can resume after crashes.

**Requirements Addressed:** U-007, U-009, U-010, SESSION-001 to SESSION-008

### Atomic Tasks

#### 3.1 Session Store Implementation

- [ ] **3.1.1** Create `src/orchestration/__init__.py`

- [ ] **3.1.2** Create `src/orchestration/session_store.py` with SQLite implementation
  ```python
  import sqlite3
  from pathlib import Path
  from src.core.interfaces import SessionStore, Session, FileRecord
  
  class SQLiteSessionStore(SessionStore):
      def __init__(self, db_path: Path = Path("data/sessions/sessions.db")):
          self.db_path = db_path
          self._init_db()
      
      def _init_db(self) -> None:
          """Create tables if not exist."""
          
      def create_session(self, operation: str, config: dict, files: list[Path]) -> Session:
          """INSERT session and file records."""
          
      def get_session(self, session_id: str) -> Session | None:
          """SELECT session with all file records."""
          
      def update_file_status(
          self, session_id: str, file_path: Path, 
          status: FileStatus, output_path: Path | None = None, error: str | None = None
      ) -> None:
          """UPDATE file status. Called by SessionManager, NOT processors."""
          
      def checkpoint(self, session_id: str) -> None:
          """COMMIT transaction (explicit checkpoint)."""
  ```

- [ ] **3.1.3** Write tests (`tests/unit/test_session_store.py`)
  ```python
  def test_create_session():
      """SESSION-001: Create session with files."""
      
  def test_update_file_status_completed():
      """SESSION-002: Update file to completed."""
      
  def test_update_file_status_failed():
      """SESSION-003: Update file to failed with error."""
      
  def test_get_latest_incomplete():
      """SESSION-005: Get most recent incomplete session."""
      
  def test_session_isolation():
      """Verify sessions don't interfere with each other."""
  ```

#### 3.2 Session Manager

- [ ] **3.2.1** Create `src/orchestration/session.py` with `SessionManager`
  ```python
  class SessionManager:
      """
      Orchestrates batch processing with checkpointing.
      
      This is the ONLY component that writes to the session database.
      Processors are pure functions - they return ProcessResult,
      and SessionManager records the result.
      """
      
      def __init__(
          self, 
          store: SessionStore,
          checkpoint_interval: int = 100,
          progress: ProgressReporter | None = None
      ):
          self.store = store
          self.checkpoint_interval = checkpoint_interval
          self.progress = progress or ProgressReporter()
      
      def run_batch(
          self,
          processor: AudioProcessor,
          input_files: list[Path],
          output_dir: Path,
          config: dict,
          resume_session_id: str | None = None
      ) -> Session:
          """
          Execute processor on all files with crash recovery.
          
          Flow:
          1. Create or resume session
          2. For each pending file:
             a. Mark as PROCESSING in DB
             b. Call processor.process() (pure function)
             c. Record ProcessResult in DB (COMPLETED or FAILED)
             d. Checkpoint every N files
          3. Mark session COMPLETED
          4. Return final session state
          """
      
      def resume_latest(self) -> Session:
          """Resume most recent incomplete session."""
      
      def _handle_interrupt(self, signum, frame):
          """Gracefully handle Ctrl+C - checkpoint and mark PAUSED."""
  ```

- [ ] **3.2.2** Implement signal handling for graceful Ctrl+C
  ```python
  import signal
  
  def _register_signal_handlers(self):
      signal.signal(signal.SIGINT, self._handle_interrupt)
      signal.signal(signal.SIGTERM, self._handle_interrupt)
  ```

- [ ] **3.2.3** Write tests (`tests/unit/test_session_manager.py`)
  ```python
  def test_run_batch_creates_session():
      """Verify session created on batch start."""
      
  def test_run_batch_updates_file_status():
      """Verify each file status updated after processing."""
      
  def test_run_batch_checkpoints():
      """AC-SESSION-4: Checkpoint every N files."""
      
  def test_resume_skips_completed():
      """AC-SESSION-1: Resume skips already-completed files."""
      
  def test_resume_completed_session_fails():
      """AC-SESSION-5: Resume on completed session shows error."""
  ```

- [ ] **3.2.4** Write integration test (`tests/integration/test_crash_recovery.py`)
  ```python
  def test_crash_and_resume():
      """
      Simulate crash at file 5 of 10.
      Resume should process only files 5-10.
      """
  ```

#### 3.3 CLI Integration

- [ ] **3.3.1** Create `src/presentation/cli/session_cmd.py`
  ```python
  @app.command("list")
  def list_sessions(limit: int = 10):
      """List recent sessions."""
      
  @app.command("resume")
  def resume_session(session_id: str | None = None, force: bool = False):
      """Resume an incomplete session."""
      
  @app.command("clean")
  def clean_sessions(older_than: str = "7d"):
      """Delete sessions older than specified duration."""
  ```

- [ ] **3.3.2** Update split and convert commands to use SessionManager
  ```python
  # In split_cmd.py
  @app.command("fixed")
  def split_fixed(..., resume: bool = typer.Option(False, "--resume")):
      session_manager = SessionManager(SQLiteSessionStore())
      
      if resume:
          session = session_manager.resume_latest()
      else:
          files = scan_audio_files(input, recursive)
          session = session_manager.run_batch(
              processor=FixedSplitter(),
              input_files=files,
              output_dir=output,
              config={"duration": duration, "format": format}
          )
  ```

### Verification Step
```bash
# Unit tests
pytest tests/unit/test_session_store.py -v
pytest tests/unit/test_session_manager.py -v

# Integration test
pytest tests/integration/test_crash_recovery.py -v

# Manual crash recovery test
# 1. Start a large batch
audiotoolkit split fixed --input ./large_audio_folder --duration 30

# 2. Press Ctrl+C after a few files
# 3. Check session was saved
audiotoolkit sessions list

# 4. Resume
audiotoolkit sessions resume
# Should show "Resuming session {id}, skipping X completed files"

# 5. Verify completed
audiotoolkit sessions list
# Session should show status=completed
```

**Exit Criteria:**
- Batch operations create sessions
- Ctrl+C gracefully saves state
- `--resume` continues from last checkpoint
- `sessions list` shows all sessions

---

## Phase 4: Pipeline Engine

**Goal:** Execute multi-step processing workflows defined in YAML.

**Requirements Addressed:** PIPE-001 to PIPE-004, AC-PIPE-1 to AC-PIPE-5

### Atomic Tasks

#### 4.1 Pipeline Configuration Parser

- [ ] **4.1.1** Create `src/orchestration/pipeline_config.py` with Pydantic models
  ```python
  from pydantic import BaseModel, field_validator
  
  class PipelineStep(BaseModel):
      name: str
      processor: str
      params: dict = {}
  
  class PipelineInput(BaseModel):
      path: str
      recursive: bool = True
      formats: list[str] = ["wav", "mp3", "flac"]
  
  class PipelineSettings(BaseModel):
      checkpoint_interval: int = 100
      continue_on_error: bool = False
      output_dir: str = "./data/output"
  
  class PipelineConfig(BaseModel):
      name: str
      description: str = ""
      version: str = "1.0"
      settings: PipelineSettings
      input: PipelineInput
      steps: list[PipelineStep]
      
      @field_validator("steps")
      def validate_steps(cls, steps):
          if not steps:
              raise ValueError("Pipeline must have at least one step")
          return steps
  ```

- [ ] **4.1.2** Write config parsing tests (`tests/unit/test_pipeline_config.py`)
  ```python
  def test_parse_valid_pipeline():
      """Parse valid pipeline.yaml."""
      
  def test_parse_invalid_yaml():
      """EC-PIPE-1: Invalid YAML raises InvalidYAMLError."""
      
  def test_parse_missing_steps():
      """Raise error if steps is empty."""
  ```

#### 4.2 Pipeline Engine

- [ ] **4.2.1** Create `src/orchestration/pipeline.py` with `PipelineEngine`
  ```python
  class PipelineEngine:
      def __init__(
          self,
          plugin_manager: PluginManager,
          session_manager: SessionManager
      ):
          self.plugins = plugin_manager
          self.sessions = session_manager
      
      def validate(self, config: PipelineConfig) -> list[str]:
          """
          Validate pipeline config without executing.
          Returns list of errors (empty if valid).
          Check: all processors exist, required params provided.
          """
      
      def dry_run(self, config: PipelineConfig) -> None:
          """
          Print execution plan without processing.
          AC-PIPE-2: "Step 1: normalize, Step 2: denoise..."
          """
      
      def execute(
          self, 
          config: PipelineConfig,
          resume: bool = False
      ) -> Session:
          """
          Execute pipeline steps in order.
          Each step's output becomes next step's input.
          """
      
      def _execute_step(
          self,
          step: PipelineStep,
          input_files: list[Path],
          output_dir: Path
      ) -> list[Path]:
          """Execute single step, return output files."""
  ```

- [ ] **4.2.2** Write tests (`tests/unit/test_pipeline_engine.py`)
  ```python
  def test_validate_unknown_processor():
      """EC-PIPE-2: Unknown processor name raises error."""
      
  def test_validate_missing_param():
      """EC-PIPE-4: Missing required param raises error."""
      
  def test_dry_run_output():
      """AC-PIPE-2: dry_run prints steps without executing."""
      
  def test_execute_order():
      """AC-PIPE-1: Steps execute in exact order."""
      
  def test_execute_step_failure():
      """AC-PIPE-3: Failure at step N halts, preserves steps 1 to N-1."""
  ```

- [ ] **4.2.3** Write integration test (`tests/integration/test_pipeline.py`)
  ```python
  def test_full_pipeline_execution():
      """Execute: convert -> split -> (verify outputs)"""
  ```

#### 4.3 CLI Integration

- [ ] **4.3.1** Create `src/presentation/cli/pipeline_cmd.py`
  ```python
  @app.command("run")
  def run_pipeline(
      config: Path = typer.Option(..., "--config", "-c"),
      dry_run: bool = typer.Option(False, "--dry-run"),
      resume: bool = typer.Option(False, "--resume"),
  ):
      """Execute a processing pipeline from YAML config."""
  
  @app.command("validate")
  def validate_pipeline(config: Path = typer.Option(..., "--config", "-c")):
      """Validate pipeline config without executing."""
  ```

### Verification Step
```bash
# Unit tests
pytest tests/unit/test_pipeline_config.py -v
pytest tests/unit/test_pipeline_engine.py -v

# Integration tests
pytest tests/integration/test_pipeline.py -v

# Manual test with sample pipeline
cat > test_pipeline.yaml << EOF
name: test-pipeline
settings:
  output_dir: ./data/output/pipeline-test
input:
  path: ./tests/fixtures/audio
  formats: ["wav"]
steps:
  - name: convert-to-mp3
    processor: converter
    params:
      format: mp3
  - name: split-chunks
    processor: splitter-fixed
    params:
      duration: 5
EOF

# Dry run
audiotoolkit pipeline run --config test_pipeline.yaml --dry-run
# Should output: "Step 1: convert-to-mp3 (converter), Step 2: split-chunks (splitter-fixed)"

# Execute
audiotoolkit pipeline run --config test_pipeline.yaml
ls ./data/output/pipeline-test  # Should have MP3 segments
```

**Exit Criteria:**
- `--dry-run` shows execution plan
- Pipeline executes steps in order
- Step failure halts execution
- `--resume` continues failed pipeline

---

## Phase 8: Polish & Release ✅ COMPLETE

**Goal:** Finalize documentation and prepare for v1.0.0 release.

### Completed Tasks

#### 8.1 Documentation Updates ✅
- [x] Updated `readme.md` with comprehensive features, installation, usage examples
- [x] Updated `docs/file-structure.md` with current project structure
- [x] Created `docs/plugins/creating-plugins.md` plugin development guide
- [x] Updated `contributing.md` with development setup and guidelines
- [x] Updated `changelog.md` with v1.0.0 release notes

#### 8.2 Testing & Quality ✅
- [x] Added CLI tests for session_cmd (46 tests)
- [x] Added CLI tests for pipeline_cmd (48 tests)
- [x] Achieved 73% code coverage (up from 64%)
- [x] 461 total tests passing

#### 8.3 Release Preparation ✅
- [x] Updated pyproject.toml to v1.0.0
- [x] Added all dependencies (PyYAML, InquirerPy)
- [x] Configured entry points for CLI and plugins
- [x] Verified editable install works
- [x] Verified CLI runs correctly

---
