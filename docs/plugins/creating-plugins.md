# Creating Plugins for Audio Toolkit

This guide explains how to create custom audio processors as plugins for Audio Toolkit.

## Overview

Audio Toolkit uses Python entry points to discover and load third-party plugins. A plugin is a Python package that:

1. Implements the `AudioProcessor` interface
2. Registers processors via the `audiotoolkit.plugins` entry point
3. Gets discovered automatically when installed in the same environment

## Quick Start

### 1. Create the Package Structure

```
my-audio-plugin/
├── pyproject.toml
├── README.md
└── my_plugin/
    ├── __init__.py
    └── processor.py
```

### 2. Implement the Processor

```python
# my_plugin/processor.py
from pathlib import Path
from typing import List
import shutil

from src.core.interfaces import AudioProcessor
from src.core.types import ParameterSpec, ProcessorCategory, ProcessResult


class MyProcessor(AudioProcessor):
    """A custom audio processor."""
    
    @property
    def name(self) -> str:
        """Unique identifier for this processor."""
        return "my-processor"
    
    @property
    def version(self) -> str:
        """Semantic version string."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Human-readable description shown in CLI."""
        return "My custom audio processor that does amazing things"
    
    @property
    def category(self) -> ProcessorCategory:
        """Category for organizing in UI."""
        return ProcessorCategory.MANIPULATION
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        """Define parameters users can configure."""
        return [
            ParameterSpec(
                name="volume",
                type="float",
                description="Volume adjustment in dB",
                required=False,
                default=0.0,
                min_value=-20.0,
                max_value=20.0,
            ),
            ParameterSpec(
                name="format",
                type="string",
                description="Output audio format",
                required=False,
                default="mp3",
                choices=["mp3", "wav", "flac"],
            ),
        ]
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        **kwargs
    ) -> ProcessResult:
        """
        Process a single audio file.
        
        Args:
            input_path: Path to the input audio file
            output_dir: Directory to write output files
            **kwargs: Parameters defined above
            
        Returns:
            ProcessResult with success status and output paths
        """
        import time
        start_time = time.time()
        
        try:
            # Get parameters with defaults
            volume = kwargs.get("volume", 0.0)
            output_format = kwargs.get("format", "mp3")
            
            # Create output path
            output_path = output_dir / f"{input_path.stem}_processed.{output_format}"
            
            # Your audio processing logic here
            # For example, using pydub:
            # from pydub import AudioSegment
            # audio = AudioSegment.from_file(input_path)
            # audio = audio + volume  # Adjust volume
            # audio.export(output_path, format=output_format)
            
            # For this example, just copy the file
            shutil.copy(input_path, output_path)
            
            processing_time = (time.time() - start_time) * 1000
            
            return ProcessResult(
                success=True,
                input_path=input_path,
                output_paths=[output_path],
                processing_time_ms=processing_time,
                metadata={"volume": volume, "format": output_format},
            )
            
        except Exception as e:
            return ProcessResult(
                success=False,
                input_path=input_path,
                output_paths=[],
                error_message=str(e),
            )
```

### 3. Configure the Entry Point

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-audio-plugin"
version = "1.0.0"
description = "A custom audio processor plugin for Audio Toolkit"
requires-python = ">=3.13"
dependencies = [
    "pydub>=0.25.0",
]

[project.entry-points."audiotoolkit.plugins"]
my-processor = "my_plugin.processor:MyProcessor"
```

### 4. Install the Plugin

```bash
# Install in development mode
pip install -e ./my-audio-plugin

# Or install from PyPI
pip install my-audio-plugin
```

### 5. Verify Installation

```bash
# Check that the plugin is discovered
audiotoolkit plugins list

# View plugin details
audiotoolkit plugins info my-processor
```

## The AudioProcessor Interface

All processors must implement the `AudioProcessor` abstract base class:

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Unique identifier (use kebab-case) |
| `version` | `str` | Semantic version (e.g., "1.0.0") |
| `description` | `str` | Human-readable description |
| `category` | `ProcessorCategory` | Category for UI organization |
| `parameters` | `List[ParameterSpec]` | Parameter specifications |

### Required Methods

#### `process(input_path, output_dir, **kwargs) -> ProcessResult`

Process a single audio file. This method should:

- Be **idempotent** - same input produces same output
- Be **pure** - no side effects beyond file I/O
- Handle errors gracefully - return `ProcessResult` with `success=False`
- Not manage sessions - that's handled by the framework

### Optional Methods

#### `validate_params(**kwargs) -> List[str]`

The base class provides default validation. Override to add custom validation:

```python
def validate_params(self, **kwargs) -> List[str]:
    errors = super().validate_params(**kwargs)
    
    # Custom validation
    if kwargs.get("custom_param") == "invalid":
        errors.append("custom_param cannot be 'invalid'")
    
    return errors
```

## Core Types

### ProcessorCategory

Categories for organizing processors in the UI:

```python
from src.core.types import ProcessorCategory

class ProcessorCategory(Enum):
    MANIPULATION = "manipulation"  # Splitting, merging, converting
    ANALYSIS = "analysis"          # Audio analysis, feature extraction
    VOICE = "voice"                # Speech processing, transcription
    AUTOMATION = "automation"      # Batch processing, workflows
```

### ParameterSpec

Define parameters that users can configure:

```python
from src.core.types import ParameterSpec

ParameterSpec(
    name="duration",           # Parameter name
    type="integer",            # Type: string, integer, float, boolean
    description="Duration in seconds",
    required=True,             # Must be provided
    default=30,                # Default value (if not required)
    choices=None,              # List of valid values (optional)
    min_value=1,               # Minimum value (for numbers)
    max_value=3600,            # Maximum value (for numbers)
)
```

### ProcessResult

Return this from the `process` method:

```python
from src.core.types import ProcessResult

ProcessResult(
    success=True,              # Whether processing succeeded
    input_path=input_path,     # Original input path
    output_paths=[output1],    # List of created output files
    error_message=None,        # Error message if failed
    metadata={},               # Any additional metadata
    processing_time_ms=150.0,  # Processing time in milliseconds
)
```

## Best Practices

### 1. Use Meaningful Names

```python
# Good
@property
def name(self) -> str:
    return "audio-normalizer"

# Bad
@property
def name(self) -> str:
    return "proc1"
```

### 2. Provide Clear Descriptions

```python
@property
def description(self) -> str:
    return "Normalize audio levels to -14 LUFS for podcast publishing"
```

### 3. Handle Errors Gracefully

```python
def process(self, input_path: Path, output_dir: Path, **kwargs) -> ProcessResult:
    try:
        # Processing logic
        return ProcessResult(success=True, ...)
    except FileNotFoundError:
        return ProcessResult(
            success=False,
            input_path=input_path,
            output_paths=[],
            error_message=f"Input file not found: {input_path}",
        )
    except Exception as e:
        return ProcessResult(
            success=False,
            input_path=input_path,
            output_paths=[],
            error_message=f"Unexpected error: {e}",
        )
```

### 4. Validate Parameters

Define parameter constraints using `ParameterSpec`:

```python
@property
def parameters(self) -> List[ParameterSpec]:
    return [
        ParameterSpec(
            name="bitrate",
            type="integer",
            description="Output bitrate in kbps",
            required=False,
            default=192,
            min_value=64,
            max_value=320,
            choices=[64, 128, 192, 256, 320],
        ),
    ]
```

### 5. Include Metadata

Return useful metadata for logging and debugging:

```python
return ProcessResult(
    success=True,
    input_path=input_path,
    output_paths=[output_path],
    metadata={
        "input_duration_ms": input_duration,
        "output_duration_ms": output_duration,
        "compression_ratio": input_size / output_size,
    },
    processing_time_ms=elapsed_ms,
)
```

## Testing Your Plugin

### Unit Tests

```python
# test_processor.py
import pytest
from pathlib import Path
from my_plugin.processor import MyProcessor


class TestMyProcessor:
    def test_properties(self):
        proc = MyProcessor()
        assert proc.name == "my-processor"
        assert proc.version == "1.0.0"
        assert len(proc.parameters) > 0
    
    def test_process_success(self, tmp_path):
        proc = MyProcessor()
        
        # Create test input
        input_file = tmp_path / "test.mp3"
        input_file.write_bytes(b"fake audio data")
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = proc.process(input_file, output_dir, volume=0.0)
        
        assert result.success
        assert len(result.output_paths) == 1
    
    def test_validate_params(self):
        proc = MyProcessor()
        
        # Valid parameters
        errors = proc.validate_params(volume=10.0)
        assert errors == []
        
        # Invalid parameters
        errors = proc.validate_params(volume=100.0)  # Exceeds max
        assert len(errors) > 0
```

### Integration Testing

```bash
# Test with real audio files
audiotoolkit plugins list  # Verify plugin appears
audiotoolkit plugins info my-processor  # Check details
```

## Plugin Management Commands

```bash
# List all available processors
audiotoolkit plugins list

# List with full details
audiotoolkit plugins list --verbose

# Filter by category
audiotoolkit plugins list --category manipulation

# Show processor details
audiotoolkit plugins info my-processor

# Disable a processor
audiotoolkit plugins disable my-processor

# Re-enable a processor
audiotoolkit plugins enable my-processor

# Force rediscovery of plugins
audiotoolkit plugins discover
```

## Example: Complete Plugin

See the sample plugin in `tests/fixtures/sample_plugin/` for a complete working example:

```
tests/fixtures/sample_plugin/
├── pyproject.toml          # Package configuration with entry point
├── README.md               # Plugin documentation
└── echo_processor.py       # EchoProcessor implementation
```

This plugin demonstrates:
- Proper interface implementation
- Parameter definition
- Entry point registration
- Error handling

## Troubleshooting

### Plugin Not Discovered

1. Verify the package is installed:
   ```bash
   pip show my-audio-plugin
   ```

2. Check entry points are registered:
   ```bash
   python -c "from importlib.metadata import entry_points; print(list(entry_points(group='audiotoolkit.plugins')))"
   ```

3. Force rediscovery:
   ```bash
   audiotoolkit plugins discover
   ```

### Import Errors

If your plugin fails to load, check the logs:
```bash
audiotoolkit plugins discover
# Check data/logs/ for error messages
```

Common issues:
- Missing dependencies
- Import errors in your module
- Incorrect entry point path

### Parameter Validation Errors

Ensure your `ParameterSpec` definitions match what your `process` method expects:

```python
# Parameters should have sensible defaults
ParameterSpec(
    name="option",
    type="string",
    description="Processing option",
    required=False,  # Optional
    default="default_value",  # Has default
)
```

## API Reference

For complete API documentation, see:
- `src/core/interfaces.py` - Interface definitions
- `src/core/types.py` - Type definitions
- `src/orchestration/plugin_manager.py` - Plugin discovery
