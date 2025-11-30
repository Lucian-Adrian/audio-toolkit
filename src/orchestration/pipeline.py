"""Pipeline engine for executing multi-step processing workflows."""

from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from ..core.exceptions import (
    ConfigError,
    MissingParameterError,
    PluginNotFoundError,
    ProcessingError,
)
from ..core.interfaces import ProgressReporter
from ..core.types import FileStatus, Session, SessionStatus
from ..processors import get_processor, list_processors
from ..utils.file_ops import scan_audio_files
from ..utils.logger import get_logger
from .pipeline_config import PipelineConfig, PipelineStep
from .session import SessionManager
from .session_store import SQLiteSessionStore

logger = get_logger(__name__)


class PipelineEngine:
    """
    Engine for executing multi-step audio processing pipelines.
    
    Features:
    - YAML-based pipeline configuration
    - Validation before execution
    - Dry-run mode
    - Step-by-step execution with checkpointing
    - Resume from failure
    """
    
    def __init__(
        self,
        session_store: Optional[SQLiteSessionStore] = None,
        progress_reporter: Optional[ProgressReporter] = None,
    ):
        """
        Initialize the pipeline engine.
        
        Args:
            session_store: Session store for persistence
            progress_reporter: Progress reporter for UI updates
        """
        self.session_store = session_store or SQLiteSessionStore()
        self.progress_reporter = progress_reporter
    
    def validate(self, config: PipelineConfig) -> List[str]:
        """
        Validate pipeline config without executing.
        
        Checks:
        - All processors exist
        - Required parameters are provided
        - Input path exists
        
        Args:
            config: Pipeline configuration to validate
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        available_processors = list_processors()
        
        # Check input path
        input_path = Path(config.input.path)
        if not input_path.exists():
            errors.append(f"Input path does not exist: {config.input.path}")
        
        # Check each step
        for i, step in enumerate(config.steps, start=1):
            # Check processor exists
            if step.processor not in available_processors:
                errors.append(
                    f"Step {i} ({step.name}): Unknown processor '{step.processor}'. "
                    f"Available: {available_processors}"
                )
                continue
            
            # Check required parameters
            try:
                processor = get_processor(step.processor)
                param_errors = processor.validate_params(**step.params)
                for err in param_errors:
                    errors.append(f"Step {i} ({step.name}): {err}")
            except PluginNotFoundError:
                pass  # Already reported above
        
        return errors
    
    def dry_run(
        self,
        config: PipelineConfig,
        output_callback: Optional[Callable[[str], None]] = None
    ) -> List[str]:
        """
        Print execution plan without processing.
        
        Args:
            config: Pipeline configuration
            output_callback: Optional callback for output (default: print)
            
        Returns:
            List of planned step descriptions
        """
        output = output_callback or print
        plan = []
        
        # Header
        output(f"Pipeline: {config.name} (v{config.version})")
        if config.description:
            output(f"Description: {config.description}")
        output("")
        
        # Input info
        input_path = Path(config.input.path)
        if input_path.exists():
            if input_path.is_dir():
                files = list(scan_audio_files(
                    input_path,
                    formats=set(config.input.formats),
                    recursive=config.input.recursive
                ))
                output(f"Input: {len(files)} files from {config.input.path}")
            else:
                output(f"Input: {config.input.path}")
        else:
            output(f"Input: {config.input.path} (NOT FOUND)")
        output("")
        
        # Steps
        output("Execution Plan:")
        for i, step in enumerate(config.steps, start=1):
            step_desc = f"Step {i}: {step.name} ({step.processor})"
            plan.append(step_desc)
            output(f"  {step_desc}")
            
            # Show parameters
            if step.params:
                for key, value in step.params.items():
                    output(f"    - {key}: {value}")
        
        output("")
        output(f"Output: {config.settings.output_dir}")
        
        return plan
    
    def execute(
        self,
        config: PipelineConfig,
        resume: bool = False,
        resume_from_step: Optional[int] = None,
    ) -> Session:
        """
        Execute pipeline steps in order.
        
        Each step's output becomes the next step's input.
        
        Args:
            config: Pipeline configuration
            resume: Whether to resume from last checkpoint
            resume_from_step: Specific step number to resume from (1-indexed)
            
        Returns:
            Final session state
            
        Raises:
            ConfigError: If validation fails
            ProcessingError: If execution fails
        """
        # Validate first
        errors = self.validate(config)
        if errors:
            raise ConfigError(f"Pipeline validation failed:\n" + "\n".join(errors))
        
        # Resolve input files
        input_path = Path(config.input.path)
        if input_path.is_dir():
            input_files = list(scan_audio_files(
                input_path,
                formats=set(config.input.formats),
                recursive=config.input.recursive
            ))
        else:
            input_files = [input_path]
        
        if not input_files:
            logger.warning("No files to process")
            # Return empty session
            session = self.session_store.create_session(
                processor_name=f"pipeline:{config.name}",
                file_paths=[],
                config=config.model_dump()
            )
            self.session_store.complete_session(session.session_id, success=True)
            return self.session_store.get_session(session.session_id)
        
        # Determine starting step
        start_step = 0
        if resume_from_step is not None:
            start_step = max(0, resume_from_step - 1)
        
        # Execute steps
        output_dir = Path(config.settings.output_dir)
        current_files = input_files
        
        logger.info(f"Starting pipeline '{config.name}' with {len(config.steps)} steps")
        
        # Track overall session for the pipeline
        pipeline_session = self.session_store.create_session(
            processor_name=f"pipeline:{config.name}",
            file_paths=input_files,
            config=config.model_dump()
        )
        
        completed_steps = []
        
        try:
            for step_idx, step in enumerate(config.steps[start_step:], start=start_step):
                step_num = step_idx + 1
                
                logger.info(f"Executing step {step_num}/{len(config.steps)}: {step.name}")
                
                # Create step output directory
                step_output_dir = output_dir / f"step_{step_num:02d}_{step.name}"
                step_output_dir.mkdir(parents=True, exist_ok=True)
                
                # Execute step
                output_files = self._execute_step(
                    step=step,
                    input_files=current_files,
                    output_dir=step_output_dir,
                    checkpoint_interval=config.settings.checkpoint_interval,
                    continue_on_error=config.settings.continue_on_error,
                )
                
                if not output_files and not config.settings.continue_on_error:
                    raise ProcessingError(
                        f"Step {step_num} ({step.name}) produced no output files"
                    )
                
                completed_steps.append(step.name)
                current_files = output_files
                
                logger.info(f"Step {step_num} complete: {len(output_files)} files")
            
            # Mark pipeline as completed
            self.session_store.complete_session(
                pipeline_session.session_id,
                success=True
            )
            
            logger.info(f"Pipeline '{config.name}' completed successfully")
            
        except Exception as e:
            logger.error(f"Pipeline failed at step: {e}")
            
            # Mark pipeline as failed but preserve completed steps
            self.session_store.complete_session(
                pipeline_session.session_id,
                success=False
            )
            
            raise ProcessingError(
                f"Pipeline halted at step {len(completed_steps) + 1}: {e}. "
                f"Completed steps: {completed_steps}"
            ) from e
        
        return self.session_store.get_session(pipeline_session.session_id)
    
    def _execute_step(
        self,
        step: PipelineStep,
        input_files: List[Path],
        output_dir: Path,
        checkpoint_interval: int = 100,
        continue_on_error: bool = False,
    ) -> List[Path]:
        """
        Execute a single pipeline step.
        
        Args:
            step: Pipeline step to execute
            input_files: Input files for this step
            output_dir: Output directory for this step
            checkpoint_interval: Files between checkpoints
            continue_on_error: Whether to continue on file errors
            
        Returns:
            List of output files from this step
        """
        processor = get_processor(step.processor)
        output_files = []
        
        session_manager = SessionManager(
            store=self.session_store,
            checkpoint_interval=checkpoint_interval,
            progress=self.progress_reporter
        )
        
        # Process files
        for file_path in input_files:
            try:
                result = processor.process(
                    input_path=file_path,
                    output_dir=output_dir,
                    **step.params
                )
                
                if result.success:
                    output_files.extend(result.output_paths)
                elif not continue_on_error:
                    raise ProcessingError(
                        f"Processing failed for {file_path}: {result.error_message}"
                    )
                else:
                    logger.warning(f"Skipping failed file: {file_path}")
                    
            except Exception as e:
                if not continue_on_error:
                    raise
                logger.warning(f"Error processing {file_path}: {e}")
        
        return output_files
    
    def get_available_processors(self) -> List[str]:
        """Get list of available processor names."""
        return list_processors()
