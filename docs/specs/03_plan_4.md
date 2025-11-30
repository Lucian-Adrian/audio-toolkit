
## Phase 4: Pipeline Engine

**Goal:** Execute multi-step processing workflows defined in YAML.

**Requirements Addressed:** PIPE-001 to PIPE-004, AC-PIPE-1 to AC-PIPE-5

**Status:** ✅ COMPLETED

### Atomic Tasks

#### 4.1 Pipeline Configuration Parser

- [x] **4.1.1** Create `src/orchestration/pipeline_config.py` with Pydantic models
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

- [x] **4.1.2** Write config parsing tests (`tests/unit/test_pipeline_config.py`)
  ```python
  def test_parse_valid_pipeline():
      """Parse valid pipeline.yaml."""
      
  def test_parse_invalid_yaml():
      """EC-PIPE-1: Invalid YAML raises InvalidYAMLError."""
      
  def test_parse_missing_steps():
      """Raise error if steps is empty."""
  ```

#### 4.2 Pipeline Engine

- [x] **4.2.1** Create `src/orchestration/pipeline.py` with `PipelineEngine`
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

- [x] **4.2.2** Write tests (`tests/unit/test_pipeline_engine.py`)
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

- [x] **4.2.3** Write integration test (`tests/integration/test_pipeline.py`)
  ```python
  def test_full_pipeline_execution():
      """Execute: convert -> split -> (verify outputs)"""
  ```

#### 4.3 CLI Integration

- [x] **4.3.1** Create `src/presentation/cli/pipeline_cmd.py`
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