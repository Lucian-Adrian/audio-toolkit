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

## Phase 0: Project Setup

**Goal:** Establish project skeleton, dependencies, and verify toolchain works.

**Requirements Addressed:** U-001, U-002, U-004

### Atomic Tasks

- [ ] **0.1** Create `pyproject.toml` with project metadata and entry point
  ```toml
  [project]
  name = "audiotoolkit"
  version = "0.1.0"
  [project.scripts]
  audiotoolkit = "src.main:app"
  ```

- [ ] **0.2** Create `requirements.txt` with core dependencies
  ```
  typer>=0.9.0
  rich>=13.0.0
  pydub>=0.25.1
  pyyaml>=6.0
  pydantic>=2.0
  ```

- [ ] **0.3** Create `requirements-dev.txt` with development dependencies
  ```
  pytest>=7.4.0
  pytest-cov>=4.1.0
  pytest-mock>=3.11.0
  black>=23.7.0
  ruff>=0.0.280
  mypy>=1.5.0
  ```

- [ ] **0.4** Create minimal `src/main.py` with Typer app skeleton
  ```python
  import typer
  app = typer.Typer(name="audiotoolkit", help="🎵 Audio Toolkit")
  
  @app.command()
  def version():
      """Show version."""
      typer.echo("audiotoolkit v0.1.0")
  
  if __name__ == "__main__":
      app()
  ```

- [ ] **0.5** Create `src/__init__.py`, `src/core/__init__.py`, `src/utils/__init__.py`

- [ ] **0.6** Create `tests/conftest.py` with basic pytest configuration

- [ ] **0.7** Create `data/` directory structure: `logs/`, `output/`, `sessions/`, `presets/`

- [ ] **0.8** Update `.gitignore` to exclude `data/`, `*.pyc`, `__pycache__/`, `.venv/`

- [ ] **0.9** Create virtual environment and install dependencies
  ```bash
  python -m venv .venv
  .venv\Scripts\activate  # Windows
  pip install -r requirements.txt -r requirements-dev.txt
  ```

- [ ] **0.10** Verify installation works
  ```bash
  python -m src.main --help
  ```

### Verification Step
```bash
# Run these commands - all must pass
python -m src.main --help          # Shows help text
python -m src.main version         # Shows "audiotoolkit v0.1.0"
pytest --collect-only              # Collects 0 tests (no errors)
mypy src/ --ignore-missing-imports # No errors
```

**Exit Criteria:** `audiotoolkit --help` displays usage information.

---

## Phase 1: Foundation Layer

**Goal:** Build the infrastructure layer that all processors depend on.

**Requirements Addressed:** U-001 to U-006, U-011, U-012

### Atomic Tasks

#### 1.1 Core Types & Exceptions (`src/core/`)

- [ ] **1.1.1** Create `src/core/types.py` with shared type definitions
  ```python
  from pathlib import Path
  from typing import TypeAlias
  
  AudioPath: TypeAlias = Path
  SupportedFormat = Literal["wav", "mp3", "flac", "ogg", "aac", "m4a"]
  DecibelLevel: TypeAlias = float  # in dB
  DurationMs: TypeAlias = int      # milliseconds
  ```

- [ ] **1.1.2** Create `src/core/exceptions.py` with exception hierarchy
  - `AudioToolkitError` (base)
  - `ConfigError`, `InvalidYAMLError`, `MissingParameterError`
  - `ProcessingError`, `CorruptedFileError`, `UnsupportedFormatError`
  - `SessionError`, `SessionLockedError`, `SessionNotFoundError`
  - `PluginError`, `PluginInterfaceError`

- [ ] **1.1.3** Create `src/core/interfaces.py` with `AudioProcessor` ABC
  - Properties: `name`, `version`, `description`, `category`
  - Methods: `process()`, `get_parameters()`, `validate_config()`
  - Dataclasses: `ParameterSpec`, `ProcessResult`, `ProcessorCategory`

- [ ] **1.1.4** Create `src/core/interfaces.py` with `SessionStore` ABC
  - Dataclasses: `Session`, `FileRecord`, `SessionStatus`, `FileStatus`
  - Methods: `create_session()`, `get_session()`, `update_file_status()`, `checkpoint()`

- [ ] **1.1.5** Write unit tests for dataclasses (`tests/unit/test_types.py`)
  - Test `ProcessResult` creation with all fields
  - Test `ParameterSpec` validation
  - Test enum values for `SessionStatus`, `FileStatus`

#### 1.2 Utilities (`src/utils/`)

- [ ] **1.2.1** Create `src/utils/logger.py` with Rich-based logging
  ```python
  from rich.console import Console
  from rich.logging import RichHandler
  import logging
  
  console = Console()
  
  def setup_logging(verbose: bool = False) -> logging.Logger:
      level = logging.DEBUG if verbose else logging.INFO
      logging.basicConfig(
          level=level,
          format="%(message)s",
          handlers=[RichHandler(console=console, rich_tracebacks=True)]
      )
      return logging.getLogger("audiotoolkit")
  ```

- [ ] **1.2.2** Create `src/utils/file_ops.py` with file utilities
  ```python
  def scan_audio_files(directory: Path, recursive: bool = True) -> list[Path]:
      """Scan directory for supported audio files."""
      
  def ensure_output_dir(path: Path) -> Path:
      """Create output directory if not exists, return path."""
      
  def generate_output_filename(
      input_path: Path, 
      suffix: str, 
      output_dir: Path,
      segment_num: int | None = None
  ) -> Path:
      """Generate output filename following naming convention."""
  ```

- [ ] **1.2.3** Create `src/utils/audio.py` with pydub wrapper
  ```python
  from pydub import AudioSegment
  
  def load_audio(path: Path) -> AudioSegment:
      """Load audio file, raise CorruptedFileError on failure."""
      
  def save_audio(audio: AudioSegment, path: Path, format: str) -> None:
      """Save audio to file."""
      
  def get_audio_info(path: Path) -> dict:
      """Return duration_ms, channels, sample_rate, format."""
  ```

- [ ] **1.2.4** Create `src/utils/config.py` with YAML loader
  ```python
  def load_yaml_config(path: Path) -> dict:
      """Load and validate YAML config, raise InvalidYAMLError on failure."""
      
  def validate_pipeline_config(config: dict) -> list[str]:
      """Return list of validation errors (empty if valid)."""
  ```

- [ ] **1.2.5** Create `src/utils/progress.py` with Rich progress bars
  ```python
  from rich.progress import Progress, TaskID
  
  class ProgressReporter:
      def start(self, total: int, description: str) -> None: ...
      def update(self, advance: int = 1) -> None: ...
      def finish(self) -> None: ...
  ```

- [ ] **1.2.6** Create `src/utils/validators.py` with input validation
  ```python
  def validate_audio_path(path: Path) -> Path:
      """Validate path exists and is supported format."""
      
  def validate_output_dir(path: Path, create: bool = True) -> Path:
      """Validate output directory is writable."""
      
  def validate_duration(seconds: float) -> float:
      """Validate duration is positive."""
  ```

- [ ] **1.2.7** Write unit tests for utilities (`tests/unit/test_utils.py`)
  - Test `scan_audio_files` with mock directory
  - Test `load_audio` with valid/invalid files
  - Test `load_yaml_config` with valid/invalid YAML
  - Test validators with edge cases

### Verification Step
```bash
# All tests must pass
pytest tests/unit/test_types.py -v
pytest tests/unit/test_utils.py -v

# Type checking
mypy src/core/ src/utils/ --strict

# Import test - all modules should import without error
python -c "from src.core.interfaces import AudioProcessor, ProcessResult"
python -c "from src.utils.logger import setup_logging"
python -c "from src.utils.audio import load_audio"
```

**Exit Criteria:** All foundation modules importable, 100% test coverage on utils.

---

## Phase 2: MVP Processors

**Goal:** Implement Fixed Splitter and Format Converter as pure functions.

**Requirements Addressed:** SPLIT-001, SPLIT-004, SPLIT-005, CONV-001 to CONV-004

### Atomic Tasks

#### 2.1 Fixed Duration Splitter

- [ ] **2.1.1** Create `src/processors/__init__.py` with processor registry

- [ ] **2.1.2** Create `src/processors/splitter/__init__.py` with exports

- [ ] **2.1.3** Create `src/processors/splitter/base.py` with shared splitter logic
  ```python
  from src.core.interfaces import AudioProcessor, ProcessResult, ParameterSpec
  
  class BaseSplitter(AudioProcessor):
      """Base class for all splitter implementations."""
      
      @property
      def category(self) -> ProcessorCategory:
          return ProcessorCategory.CORE
      
      def _save_segments(
          self, 
          segments: list[AudioSegment], 
          input_path: Path,
          output_dir: Path,
          format: str
      ) -> list[Path]:
          """Save segments to files, return output paths."""
  ```

- [ ] **2.1.4** Create `src/processors/splitter/fixed.py` implementing `FixedSplitter`
  ```python
  class FixedSplitter(BaseSplitter):
      @property
      def name(self) -> str:
          return "splitter-fixed"
      
      @property
      def version(self) -> str:
          return "1.0.0"
      
      @property
      def description(self) -> str:
          return "Split audio into fixed-duration segments"
      
      def get_parameters(self) -> list[ParameterSpec]:
          return [
              ParameterSpec(
                  name="duration",
                  param_type="float",
                  required=True,
                  description="Segment duration in seconds",
                  min_value=0.1
              ),
              ParameterSpec(
                  name="format",
                  param_type="choice",
                  required=False,
                  default="wav",
                  choices=["wav", "mp3", "flac"]
              )
          ]
      
      def process(
          self, 
          input_path: Path, 
          output_dir: Path, 
          duration: float,
          format: str = "wav",
          **kwargs
      ) -> ProcessResult:
          """Pure function: Read file → Split → Write segments → Return result."""
  ```

- [ ] **2.1.5** Write comprehensive tests (`tests/unit/test_splitter_fixed.py`)
  ```python
  def test_fixed_splitter_correct_segment_count():
      """AC-SPLIT-1: 10-min file with 60s duration = 10 segments."""
      
  def test_fixed_splitter_handles_remainder():
      """AC-SPLIT-2: 10-min file with 180s = 3x180s + 1x60s."""
      
  def test_fixed_splitter_short_file():
      """EC-SPLIT-1: File shorter than duration = 1 segment + warning."""
      
  def test_fixed_splitter_output_naming():
      """AC-SPLIT-5: Output follows {name}_segment_{NNN}.{ext} pattern."""
      
  def test_fixed_splitter_is_pure_function():
      """Verify process() has no side effects beyond file output."""
  ```

- [ ] **2.1.6** Create test fixtures (`tests/fixtures/audio/`)
  - Generate 10-second mono WAV file
  - Generate 60-second stereo MP3 file
  - Generate file with silence gaps

#### 2.2 Format Converter

- [ ] **2.2.1** Create `src/processors/converter.py` implementing `FormatConverter`
  ```python
  class FormatConverter(AudioProcessor):
      @property
      def name(self) -> str:
          return "converter"
      
      def get_parameters(self) -> list[ParameterSpec]:
          return [
              ParameterSpec(name="format", param_type="choice", required=True, 
                           choices=["wav", "mp3", "flac", "ogg", "aac", "m4a"]),
              ParameterSpec(name="normalize", param_type="bool", default=False),
              ParameterSpec(name="target_lufs", param_type="float", default=-14.0),
          ]
      
      def process(
          self, 
          input_path: Path, 
          output_dir: Path,
          format: str,
          normalize: bool = False,
          target_lufs: float = -14.0,
          **kwargs
      ) -> ProcessResult:
          """Pure function: Convert format, optionally normalize."""
  ```

- [ ] **2.2.2** Write tests (`tests/unit/test_converter.py`)
  ```python
  def test_converter_wav_to_mp3():
      """CONV-001: Convert WAV to MP3."""
      
  def test_converter_skip_same_format():
      """CONV-004: Skip if source == target format."""
      
  def test_converter_normalize_audio():
      """CONV-002: Normalize to -14 LUFS."""
      
  def test_converter_is_pure_function():
      """Verify no side effects."""
  ```

#### 2.3 CLI Integration

- [ ] **2.3.1** Create `src/presentation/__init__.py`

- [ ] **2.3.2** Create `src/presentation/cli/__init__.py`

- [ ] **2.3.3** Create `src/presentation/cli/split_cmd.py`
  ```python
  import typer
  from pathlib import Path
  
  app = typer.Typer()
  
  @app.command("fixed")
  def split_fixed(
      input: Path = typer.Option(..., "--input", "-i", help="Input file or directory"),
      output: Path = typer.Option("./data/output", "--output", "-o"),
      duration: float = typer.Option(..., "--duration", "-d", help="Segment duration (seconds)"),
      format: str = typer.Option("wav", "--format", "-f"),
      recursive: bool = typer.Option(True, "--recursive/--no-recursive"),
  ):
      """Split audio into fixed-duration segments."""
  ```

- [ ] **2.3.4** Create `src/presentation/cli/convert_cmd.py`
  ```python
  @app.command()
  def convert(
      input: Path = typer.Option(..., "--input", "-i"),
      output: Path = typer.Option("./data/output", "--output", "-o"),
      format: str = typer.Option(..., "--format", "-f"),
      normalize: bool = typer.Option(False, "--normalize"),
      recursive: bool = typer.Option(True, "--recursive/--no-recursive"),
  ):
      """Convert audio files to different format."""
  ```

- [ ] **2.3.5** Update `src/main.py` to register CLI commands
  ```python
  from src.presentation.cli import split_cmd, convert_cmd
  
  app.add_typer(split_cmd.app, name="split")
  app.add_typer(convert_cmd.app, name="convert")
  ```

- [ ] **2.3.6** Write CLI integration tests (`tests/integration/test_cli.py`)
  ```python
  from typer.testing import CliRunner
  
  def test_split_fixed_cli():
      """Test: audiotoolkit split fixed --input test.wav --duration 10"""
      
  def test_convert_cli():
      """Test: audiotoolkit convert --input test.wav --format mp3"""
  ```

### Verification Step
```bash
# Unit tests for processors
pytest tests/unit/test_splitter_fixed.py -v --cov=src/processors/splitter
pytest tests/unit/test_converter.py -v --cov=src/processors/converter

# Integration tests
pytest tests/integration/test_cli.py -v

# Manual CLI test
audiotoolkit split fixed --input tests/fixtures/audio/10sec_mono.wav --duration 3 --output ./data/output
ls ./data/output  # Should show: 10sec_mono_segment_001.wav, ..._002.wav, ..._003.wav, ..._004.wav

audiotoolkit convert --input tests/fixtures/audio/10sec_mono.wav --format mp3 --output ./data/output
ls ./data/output  # Should show: 10sec_mono.mp3

# Type checking
mypy src/processors/ --strict
```

**Exit Criteria:** 
- `audiotoolkit split fixed` produces correct segments
- `audiotoolkit convert` produces correct output format
- All tests pass with >90% coverage on processors

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

## Phase 5: Interactive Wizard (TUI)

**Goal:** Create a user-friendly terminal interface for guided configuration.

**Requirements Addressed:** U-013, WIZARD-001 to WIZARD-008

### Atomic Tasks

#### 5.1 Wizard Infrastructure

- [ ] **5.1.1** Add InquirerPy to requirements.txt
  ```
  InquirerPy>=0.3.4
  ```

- [ ] **5.1.2** Create `src/presentation/wizard/__init__.py`

- [ ] **5.1.3** Create `src/presentation/wizard/components.py` with reusable prompts
  ```python
  from InquirerPy import inquirer
  from InquirerPy.validator import PathValidator
  
  def prompt_file_or_directory(message: str = "Select input") -> Path:
      """Prompt for file or directory selection."""
      
  def prompt_choice(message: str, choices: list[str]) -> str:
      """Prompt for single choice selection."""
      
  def prompt_number(message: str, min_val: float, max_val: float, default: float) -> float:
      """Prompt for numeric input with validation."""
      
  def prompt_confirm(message: str, default: bool = True) -> bool:
      """Prompt for yes/no confirmation."""
  ```

- [ ] **5.1.4** Create `src/presentation/wizard/preset_manager.py`
  ```python
  class PresetManager:
      PRESET_DIR = Path.home() / ".audiotoolkit" / "presets"
      
      def save_preset(self, name: str, operation: str, config: dict) -> Path:
          """Save configuration as YAML preset."""
          
      def load_preset(self, name: str) -> dict:
          """Load preset by name."""
          
      def list_presets(self) -> list[str]:
          """List all saved presets."""
          
      def delete_preset(self, name: str) -> None:
          """Delete a preset."""
  ```

#### 5.2 Wizard Flows

- [ ] **5.2.1** Create `src/presentation/wizard/main_menu.py`
  ```python
  from rich.console import Console
  from rich.panel import Panel
  
  console = Console()
  
  def launch():
      """Launch the main wizard menu."""
      console.print(Panel.fit(
          "🎵 Audio Toolkit v1.0\nInteractive Wizard Mode",
          border_style="blue"
      ))
      
      choice = inquirer.select(
          message="What would you like to do?",
          choices=[
              {"name": "🔪 Split audio files", "value": "split"},
              {"name": "🔄 Convert formats", "value": "convert"},
              {"name": "📊 Analyze audio", "value": "analyze"},
              {"name": "🎤 Voice enhancement", "value": "voice"},
              {"name": "⛓️  Run pipeline", "value": "pipeline"},
              {"name": "⚙️  Settings", "value": "settings"},
              {"name": "❌ Exit", "value": "exit"},
          ]
      ).execute()
      
      if choice == "split":
          from .split_wizard import run_split_wizard
          run_split_wizard()
      # ... etc
  ```

- [ ] **5.2.2** Create `src/presentation/wizard/split_wizard.py`
  ```python
  def run_split_wizard():
      """Interactive wizard for split operations."""
      
      # Step 1: Select mode
      mode = prompt_choice("Select split mode", [
          "Fixed duration (e.g., 30-second chunks)",
          "Silence detection (split at pauses)",
          "Timestamp file (CSV/JSON/TXT)"
      ])
      
      # Step 2: Mode-specific parameters
      if mode.startswith("Fixed"):
          duration = prompt_number("Enter chunk duration (seconds)", 1, 3600, 30)
          
      # Step 3: Select input
      input_path = prompt_file_or_directory("Select input file or directory")
      
      # Step 4: Select output
      output_dir = prompt_file_or_directory("Select output directory")
      
      # Step 5: Show summary
      show_config_summary(config)
      
      # Step 6: Confirm and execute
      if prompt_confirm("Proceed with this configuration?"):
          execute_split(config)
          
          # Step 7: Offer to save preset
          if prompt_confirm("Save as preset for future use?", default=False):
              name = inquirer.text("Preset name").execute()
              PresetManager().save_preset(name, "split", config)
  ```

- [ ] **5.2.3** Create `src/presentation/wizard/convert_wizard.py`
  ```python
  def run_convert_wizard():
      """Interactive wizard for convert operations."""
  ```

- [ ] **5.2.4** Write tests (`tests/unit/test_wizard.py`)
  ```python
  def test_preset_save_load():
      """Test preset saving and loading."""
      
  def test_preset_list():
      """Test listing presets."""
  ```

#### 5.3 CLI Integration

- [ ] **5.3.1** Update `src/main.py` to launch wizard on no args
  ```python
  @app.callback(invoke_without_command=True)
  def main(
      ctx: typer.Context,
      wizard: bool = typer.Option(False, "--wizard", "-w"),
      preset: str | None = typer.Option(None, "--preset", "-p"),
  ):
      if preset:
          config = PresetManager().load_preset(preset)
          execute_from_preset(config)
      elif ctx.invoked_subcommand is None or wizard:
          from src.presentation.wizard.main_menu import launch
          launch()
  ```

### Verification Step
```bash
# Unit tests
pytest tests/unit/test_wizard.py -v

# Manual wizard test
audiotoolkit  # Should launch wizard (no args)
audiotoolkit --wizard  # Should launch wizard

# Test preset workflow
# 1. Run wizard, save preset as "my-split"
# 2. Run with preset
audiotoolkit --preset my-split
# Should execute without prompts

# Verify non-TTY detection
echo "test" | audiotoolkit
# Should show: "Wizard requires interactive terminal. Use CLI flags instead."
```

**Exit Criteria:**
- `audiotoolkit` (no args) launches wizard
- Wizard guides through all parameters
- Presets save/load correctly
- Non-interactive terminals show helpful error

---

## Phase 6: Plugin System

**Goal:** Enable third-party plugins to extend Audio Toolkit.

**Requirements Addressed:** PLUGIN-001 to PLUGIN-007, OPT-004

### Atomic Tasks

#### 6.1 Plugin Manager

- [ ] **6.1.1** Create `src/orchestration/plugin_manager.py`
  ```python
  from importlib.metadata import entry_points
  
  class PluginManager:
      _processors: dict[str, type[AudioProcessor]] = {}
      _instances: dict[str, AudioProcessor] = {}
      _disabled: set[str] = set()
      
      @classmethod
      def discover(cls) -> None:
          """Load built-in and third-party processors."""
          # Load built-ins
          cls._register_builtins()
          
          # Load from entry_points
          eps = entry_points(group="audiotoolkit.plugins")
          for ep in eps:
              cls._load_plugin(ep)
      
      @classmethod
      def _load_plugin(cls, ep) -> None:
          """Load single plugin with error handling."""
          try:
              plugin_class = ep.load()
              instance = plugin_class()
              
              # Validate interface
              if not isinstance(instance, AudioProcessor):
                  raise PluginInterfaceError(f"Must implement AudioProcessor")
              
              # Check for duplicates
              if instance.name in cls._instances:
                  logger.warning(f"Duplicate plugin: {instance.name}")
                  return
              
              cls._processors[instance.name] = plugin_class
              cls._instances[instance.name] = instance
              
          except Exception as e:
              logger.error(f"Failed to load plugin {ep.name}: {e}")
      
      @classmethod
      def get(cls, name: str) -> AudioProcessor:
          """Get processor by name."""
          
      @classmethod
      def list_all(cls) -> dict[str, AudioProcessor]:
          """List all registered processors."""
          
      @classmethod
      def disable(cls, name: str) -> None:
          """Disable a plugin (skip on next load)."""
  ```

- [ ] **6.1.2** Write tests (`tests/unit/test_plugin_manager.py`)
  ```python
  def test_discover_builtins():
      """All built-in processors discovered."""
      
  def test_get_processor():
      """Get processor by name."""
      
  def test_get_unknown_processor():
      """EC-PLUGIN-2: Unknown processor raises KeyError."""
      
  def test_invalid_plugin_skipped():
      """EC-PLUGIN-1: Invalid plugin logged and skipped."""
  ```

- [ ] **6.1.3** Create example plugin in `tests/fixtures/sample_plugin/`
  ```python
  # tests/fixtures/sample_plugin/my_plugin.py
  from src.core.interfaces import AudioProcessor, ProcessResult
  
  class EchoProcessor(AudioProcessor):
      @property
      def name(self) -> str:
          return "echo-test"
      
      @property
      def version(self) -> str:
          return "0.1.0"
      
      @property
      def description(self) -> str:
          return "Test plugin that copies input to output"
      
      def get_parameters(self) -> list:
          return []
      
      def process(self, input_path, output_dir, **kwargs) -> ProcessResult:
          import shutil
          output = output_dir / input_path.name
          shutil.copy(input_path, output)
          return ProcessResult(success=True, output_path=output, input_path=input_path)
  ```

#### 6.2 CLI Integration

- [ ] **6.2.1** Create `src/presentation/cli/plugin_cmd.py`
  ```python
  @app.command("list")
  def list_plugins():
      """List all available plugins."""
      table = Table(title="Registered Processors")
      table.add_column("Name")
      table.add_column("Version")
      table.add_column("Category")
      table.add_column("Description")
      
      for name, processor in PluginManager.list_all().items():
          table.add_row(name, processor.version, processor.category.value, processor.description)
      
      console.print(table)
  
  @app.command("info")
  def plugin_info(name: str):
      """Show detailed plugin information."""
      processor = PluginManager.get(name)
      # Display parameters, usage examples
  ```

### Verification Step
```bash
# Unit tests
pytest tests/unit/test_plugin_manager.py -v

# Verify built-in plugins
audiotoolkit plugins list
# Should show: splitter-fixed, splitter-silence, converter, etc.

# Verify plugin info
audiotoolkit plugins info splitter-fixed
# Should show: name, version, description, parameters

# Test with sample plugin (requires installing it)
pip install -e tests/fixtures/sample_plugin/
audiotoolkit plugins list
# Should include: echo-test
```

**Exit Criteria:**
- `plugins list` shows all built-in processors
- `plugins info` shows parameter details
- Third-party plugins discoverable via entry_points

---

## Phase 7: Advanced Processors

**Goal:** Implement remaining processors for analysis, voice enhancement, and transcription.

**Requirements Addressed:** VIS-*, STAT-*, NOISE-*, DYN-*, TRIM-*, TRANS-*

### Atomic Tasks

#### 7.1 Analysis Processors

- [ ] **7.1.1** Create `src/processors/visualizer.py`
  - Mel-spectrogram generation (librosa + matplotlib)
  - Waveform generation
  - Batch output with matching filenames

- [ ] **7.1.2** Create `src/processors/statistics.py`
  - RMS, peak amplitude, silence ratio calculation
  - Voice Activity Detection (VAD)
  - JSON export

- [ ] **7.1.3** Write tests (`tests/unit/test_analysis.py`)

#### 7.2 Voice Enhancement Processors

- [ ] **7.2.1** Create `src/processors/noise_reduce.py`
  - Spectral subtraction implementation
  - Configurable strength levels

- [ ] **7.2.2** Create `src/processors/dynamics.py`
  - Dynamic range compression
  - 3-band EQ with presets

- [ ] **7.2.3** Create `src/processors/trimmer.py`
  - Auto-trim silence from start/end
  - Configurable threshold

- [ ] **7.2.4** Write tests (`tests/unit/test_voice.py`)

#### 7.3 Transcriber

- [ ] **7.3.1** Create `src/processors/transcriber.py`
  - Whisper integration (local model)
  - Output formats: SRT, TXT
  - Filename matching

- [ ] **7.3.2** Write tests (`tests/unit/test_transcriber.py`)

#### 7.4 CLI Integration

- [ ] **7.4.1** Create `src/presentation/cli/analyze_cmd.py`
- [ ] **7.4.2** Create `src/presentation/cli/voice_cmd.py`
- [ ] **7.4.3** Update wizard with new operations

### Verification Step
```bash
# Unit tests for each processor
pytest tests/unit/test_analysis.py -v
pytest tests/unit/test_voice.py -v
pytest tests/unit/test_transcriber.py -v

# CLI tests
audiotoolkit analyze stats --input test.wav
audiotoolkit analyze visualize --type mel --input test.wav

audiotoolkit voice denoise --input test.wav
audiotoolkit voice trim --input test.wav

audiotoolkit transcribe --model whisper --input test.wav --output-format srt
```

**Exit Criteria:**
- All analysis commands produce correct output
- Voice enhancement improves audio quality
- Transcriber generates accurate SRT/TXT

---

## Phase 8: Polish & Release

**Goal:** Finalize documentation, testing, and prepare for PyPI release.

### Atomic Tasks

#### 8.1 Documentation

- [ ] **8.1.1** Update `README.md` with full usage examples
- [ ] **8.1.2** Update `docs/file-structure.md` with final structure
- [ ] **8.1.3** Create `docs/plugins/creating-plugins.md` guide
- [ ] **8.1.4** Update `CONTRIBUTING.md` with development setup
- [ ] **8.1.5** Create `CHANGELOG.md` with v1.0.0 release notes

#### 8.2 Testing & Quality

- [ ] **8.2.1** Achieve >90% test coverage
  ```bash
  pytest --cov=src --cov-report=html
  ```

- [ ] **8.2.2** Run full type checking
  ```bash
  mypy src/ --strict
  ```

- [ ] **8.2.3** Run linter and fix all issues
  ```bash
  ruff check src/ --fix
  black src/
  ```

- [ ] **8.2.4** Test on Windows, macOS, Linux

#### 8.3 Release

- [ ] **8.3.1** Update version to `1.0.0` in `pyproject.toml`
- [ ] **8.3.2** Build package
  ```bash
  python -m build
  ```
- [ ] **8.3.3** Test package installation
  ```bash
  pip install dist/audiotoolkit-1.0.0-py3-none-any.whl
  audiotoolkit --help
  ```
- [ ] **8.3.4** Publish to PyPI
  ```bash
  twine upload dist/*
  ```
- [ ] **8.3.5** Create GitHub release with changelog

### Verification Step
```bash
# Final verification checklist
pytest --cov=src --cov-fail-under=90
mypy src/ --strict
ruff check src/

# Fresh install test
pip uninstall audiotoolkit
pip install audiotoolkit
audiotoolkit --help
audiotoolkit split fixed --help
audiotoolkit plugins list
```

**Exit Criteria:**
- Package installable via `pip install audiotoolkit`
- All documentation complete
- >90% test coverage
- Released on PyPI

---

## Appendix: Task Tracking

### Progress Summary

| Phase | Total Tasks | Completed | Remaining |
|-------|-------------|-----------|-----------|
| Phase 0 | 10 | 0 | 10 |
| Phase 1 | 17 | 0 | 17 |
| Phase 2 | 16 | 0 | 16 |
| Phase 3 | 10 | 0 | 10 |
| Phase 4 | 9 | 0 | 9 |
| Phase 5 | 9 | 0 | 9 |
| Phase 6 | 5 | 0 | 5 |
| Phase 7 | 11 | 0 | 11 |
| Phase 8 | 13 | 0 | 13 |
| **Total** | **100** | **0** | **100** |

### Dependencies Graph

```
Phase 0 (Setup)
    │
    ▼
Phase 1 (Foundation)
    │
    ▼
Phase 2 (MVP) ──────────────────┐
    │                           │
    ▼                           │
Phase 3 (Session) ◄─────────────┤
    │                           │
    ├───────────────┬───────────┘
    ▼               ▼
Phase 4         Phase 7
(Pipeline)      (Advanced)
    │
    ├───────────────┐
    ▼               ▼
Phase 5         Phase 6
(Wizard)        (Plugin)
    │               │
    └───────┬───────┘
            ▼
        Phase 8
        (Release)
```
