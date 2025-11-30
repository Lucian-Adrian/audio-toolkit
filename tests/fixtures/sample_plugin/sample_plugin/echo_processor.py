"""Echo processor - a simple test plugin that copies input to output."""

import shutil
import time
from pathlib import Path
from typing import List

from src.core.interfaces import AudioProcessor
from src.core.types import ParameterSpec, ProcessorCategory, ProcessResult


class EchoProcessor(AudioProcessor):
    """
    Test plugin that copies input audio to output.
    
    This processor demonstrates the minimal implementation required
    for an Audio Toolkit plugin. It simply copies the input file
    to the output directory without modification.
    
    Use Case:
        - Testing plugin infrastructure
        - Demonstrating plugin development
        - Placeholder for complex processing
    """
    
    @property
    def name(self) -> str:
        """Unique processor identifier."""
        return "echo-test"
    
    @property
    def version(self) -> str:
        """Semantic version string."""
        return "0.1.0"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Test plugin that copies input to output unchanged"
    
    @property
    def category(self) -> ProcessorCategory:
        """Category for UI organization."""
        return ProcessorCategory.AUTOMATION
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        """List of parameters this processor accepts."""
        return [
            ParameterSpec(
                name="suffix",
                type="string",
                description="Suffix to add to output filename",
                required=False,
                default="_echo",
            ),
            ParameterSpec(
                name="preserve_extension",
                type="boolean",
                description="Whether to preserve the original file extension",
                required=False,
                default=True,
            ),
        ]
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        suffix: str = "_echo",
        preserve_extension: bool = True,
        **kwargs
    ) -> ProcessResult:
        """
        Process a single audio file by copying it.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output files
            suffix: Suffix to add to output filename
            preserve_extension: Whether to keep original extension
            
        Returns:
            ProcessResult with success status and output paths
        """
        start_time = time.time()
        
        try:
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate output filename
            if preserve_extension:
                output_name = f"{input_path.stem}{suffix}{input_path.suffix}"
            else:
                output_name = f"{input_path.stem}{suffix}"
            
            output_path = output_dir / output_name
            
            # Copy file
            shutil.copy2(input_path, output_path)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return ProcessResult(
                success=True,
                input_path=input_path,
                output_paths=[output_path],
                metadata={
                    "processor": self.name,
                    "version": self.version,
                    "suffix": suffix,
                    "preserve_extension": preserve_extension,
                },
                processing_time_ms=elapsed_ms,
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=str(e),
                processing_time_ms=elapsed_ms,
            )
