# Audio Toolkit File Structure

## Overview
This document describes the organization and purpose of files and directories in the audio toolkit project.

## Root Directory

```
audio-toolkit/
├── src/                    # Source code
├── tests/                  # Test files
├── docs/                   # Documentation
├── config/                 # Configuration files
├── data/                   # Data files and presets
├── pyproject.toml          # Python project configuration
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies
├── readme.md               # Project README
├── changelog.md            # Change log
├── contributing.md         # Contributing guidelines
└── LICENSE                 # License file
```

## Source Code (src/)

### Main Entry Point (src/main.py)
Main application entry point that initializes and runs the CLI with wizard support.

### Core Module (src/core/)
Fundamental types, exceptions, and interfaces.

```
src/core/
├── __init__.py             # Package exports
├── types.py                # Data classes (AudioMetadata, ProcessorCategory, etc.)
├── exceptions.py           # Custom exceptions (AudioProcessingError, etc.)
└── interfaces.py           # Abstract base classes (AudioProcessor, etc.)
```

### Utils Module (src/utils/)
Utility functions and helpers.

```
src/utils/
├── __init__.py             # Package exports
├── audio.py                # Audio file utilities (pydub wrappers)
├── config.py               # Configuration management
├── file_ops.py             # File system operations
├── logger.py               # Logging configuration
├── progress.py             # Progress reporting utilities
└── validators.py           # Input validation functions
```

### Processors Module (src/processors/)
Audio processing components implementing the AudioProcessor interface.

```
src/processors/
├── __init__.py             # Processor registry and factory
├── converter.py            # Audio format converter
├── visualizer.py           # Audio visualization (waveform, spectrogram)
├── statistics.py           # Audio statistics analyzer (RMS, peak, VAD)
├── noise_reduce.py         # Noise reduction via spectral subtraction
├── dynamics.py             # Dynamics processing (compression, EQ)
├── trimmer.py              # Automatic silence trimming
├── transcriber.py          # Whisper-based transcription
└── splitter/               # Audio splitting components
    ├── __init__.py         # Splitter exports
    ├── base.py             # Base splitter class
    └── fixed.py            # Fixed duration splitter
```

### Orchestration Module (src/orchestration/)
Session management, pipeline engine, and plugin system.

```
src/orchestration/
├── __init__.py             # Package exports
├── pipeline.py             # Pipeline engine for multi-step workflows
├── pipeline_config.py      # YAML pipeline configuration parsing
├── plugin_manager.py       # Plugin discovery and management
├── session.py              # Session state management
└── session_store.py        # Persistent session storage
```

### Presentation Module (src/presentation/)
User interface components including CLI and interactive wizard.

```
src/presentation/
├── __init__.py             # Package exports
├── cli/                    # Command-line interface
│   ├── __init__.py         # CLI app setup with Typer
│   ├── analyze_cmd.py      # Analyze command (visualize, stats, transcribe)
│   ├── convert_cmd.py      # Convert command implementation
│   ├── pipeline_cmd.py     # Pipeline command implementation
│   ├── plugin_cmd.py       # Plugin management commands
│   ├── session_cmd.py      # Session management commands
│   ├── split_cmd.py        # Split command implementation
│   └── voice_cmd.py        # Voice enhancement commands
└── wizard/                 # Interactive wizard
    ├── __init__.py         # Wizard exports
    ├── components.py       # Reusable UI components
    ├── convert_wizard.py   # Convert operation wizard
    ├── main_menu.py        # Main menu and wizard entry
    ├── preset_manager.py   # Preset save/load functionality
    └── split_wizard.py     # Split operation wizard
```

## Tests (tests/)

### Configuration (tests/conftest.py)
Pytest fixtures and test configuration shared across all tests.

### Unit Tests (tests/unit/)
Tests for individual components.

```
tests/unit/
├── __init__.py
├── test_audio.py           # Audio utility tests
├── test_cli_convert.py     # Convert CLI tests
├── test_cli_pipeline.py    # Pipeline CLI tests
├── test_cli_plugin.py      # Plugin CLI tests
├── test_cli_session.py     # Session CLI tests
├── test_cli_split.py       # Split CLI tests
├── test_config.py          # Configuration tests
├── test_converter.py       # Converter processor tests
├── test_exceptions.py      # Custom exception tests
├── test_file_ops.py        # File operations tests
├── test_interfaces.py      # Interface tests
├── test_logger.py          # Logger tests
├── test_phase7_cli.py      # Analyze/Voice CLI tests
├── test_phase7_processors.py # Advanced processor tests
├── test_pipeline_config.py # Pipeline config tests
├── test_pipeline_engine.py # Pipeline engine tests
├── test_plugin_manager.py  # Plugin manager tests
├── test_processor_registry.py # Processor registry tests
├── test_progress.py        # Progress utility tests
├── test_session_manager.py # Session manager tests
├── test_session_store.py   # Session store tests
├── test_splitter_fixed.py  # Fixed splitter tests
├── test_types.py           # Core types tests
├── test_utils.py           # Utility tests
├── test_validators.py      # Validator tests
└── test_wizard.py          # Wizard tests
```

### Integration Tests (tests/integration/)
Tests for component interactions and end-to-end workflows.

```
tests/integration/
├── __init__.py
├── test_cli.py             # End-to-end CLI tests
├── test_crash_recovery.py  # Session recovery tests
└── test_pipeline.py        # Pipeline execution tests
```

### Test Fixtures (tests/fixtures/)
Test data and sample files.

```
tests/fixtures/
├── sample_plugin/          # Example plugin for testing
│   ├── pyproject.toml      # Plugin package config
│   ├── README.md           # Plugin documentation
│   └── echo_processor.py   # Sample processor implementation
└── audio/                  # Sample audio files (if present)
```

## Documentation (docs/)

```
docs/
├── file-structure.md       # This file
├── backend/                # Backend development docs
├── db/                     # Database documentation
├── frontend/               # Frontend development docs
├── info/                   # Project information
│   └── description.md      # Project description
├── plugins/                # Plugin development docs
│   └── creating-plugins.md # Plugin creation guide
├── specs/                  # Module specifications
│   ├── 00_overview.md      # Project overview
│   ├── 01_core_interfaces.md  # Core interfaces spec
│   ├── 02_design.md        # Design document
│   ├── 03_plan.md          # Development plan
│   ├── core_spec.md        # Core module spec
│   ├── utils_spec.md       # Utils module spec
│   ├── processors_spec.md  # Processors spec
│   └── cli_spec.md         # CLI spec
└── tests/                  # Testing documentation
```

## Configuration (config/)

```
config/
├── docker-compose.yml      # Docker Compose multi-container setup
└── Dockerfile              # Docker image definition
```

## Data (data/)

Runtime data directories (created as needed):

```
data/
├── logs/                   # Application logs
├── output/                 # Processed audio output
├── presets/                # Saved user presets (JSON)
└── sessions/               # Session state files (JSON)
```

## Key Files

### pyproject.toml
Modern Python project configuration including:
- Package metadata and dependencies
- Entry points for CLI (`audiotoolkit`) and plugins
- Tool configurations (pytest, mypy, ruff)

### requirements.txt
Production dependencies:
- `pydub` - Audio manipulation
- `typer[all]` - CLI framework
- `rich` - Terminal formatting
- `pydantic` - Data validation
- `InquirerPy` - Interactive prompts
- `PyYAML` - YAML parsing

### requirements-dev.txt
Development dependencies:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `mypy` - Type checking
- `ruff` - Linting
- `black` - Code formatting

## Entry Points

The project defines these entry points in `pyproject.toml`:

### Console Scripts
- `audiotoolkit` → `src.main:main` - Main CLI entry point

### Plugin System
- `audiotoolkit.plugins` - Entry point group for third-party processors
  - `splitter-fixed` → `src.processors.splitter.fixed:FixedSplitter`
  - `converter` → `src.processors.converter:FormatConverter`
  - `visualizer` → `src.processors.visualizer:AudioVisualizer`
  - `statistics` → `src.processors.statistics:AudioStatistics`
  - `noise_reduce` → `src.processors.noise_reduce:NoiseReducer`
  - `dynamics` → `src.processors.dynamics:DynamicsProcessor`
  - `trimmer` → `src.processors.trimmer:AudioTrimmer`
  - `transcriber` → `src.processors.transcriber:AudioTranscriber`


