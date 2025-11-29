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
├── README.md               # Project README
├── CHANGELOG.md            # Change log
├── CONTRIBUTING.md         # Contributing guidelines
├── LICENSE                 # License file
└── .github/                # GitHub configuration
```

## Source Code (src/)

### Core Module (src/core/)
Fundamental types, exceptions, and interfaces.

- `__init__.py` - Package initialization
- `types.py` - Data classes for audio metadata and configuration
- `exceptions.py` - Custom exception classes
- `interfaces.py` - Abstract base classes for components

### Utils Module (src/utils/)
Utility functions and helpers.

- `__init__.py` - Package initialization
- `logger.py` - Logging configuration
- `file_ops.py` - File system operations
- `audio.py` - Audio file utilities (using pydub)
- `config.py` - Configuration management
- `progress.py` - Progress reporting utilities
- `validators.py` - Input validation functions

### Processors Module (src/processors/)
Audio processing components.

- `__init__.py` - Processor registry and factory
- `converter.py` - Audio format converter
- `splitter/` - Audio splitting components
  - `__init__.py` - (empty)
  - `base.py` - Base splitter class
  - `fixed.py` - Fixed duration splitter

### Presentation Module (src/presentation/)
User interface components.

- `__init__.py` - (empty)
- `cli/` - Command-line interface
  - `__init__.py` - CLI setup and commands
  - `convert_cmd.py` - Convert command implementation
  - `split_cmd.py` - Split command implementation

### Main Entry Point (src/main.py)
Main application entry point that initializes and runs the CLI.

## Tests (tests/)

### Unit Tests (tests/unit/)
Tests for individual components.

- `test_types.py` - Test core data types
- `test_exceptions.py` - Test custom exceptions
- `test_interfaces.py` - Test abstract interfaces

### Integration Tests (tests/integration/)
Tests for component interactions.

- `test_audio_processing.py` - Test audio processing workflows

### Fixtures (tests/fixtures/)
Test data and fixtures.

## Documentation (docs/)

### Specifications (docs/specs/)
Detailed specifications for modules.

- `core_spec.md` - Core module specifications
- `utils_spec.md` - Utils module specifications
- `processors_spec.md` - Processors module specifications
- `cli_spec.md` - CLI specifications

### Info (docs/info/)
Project information.

- `description.md` - Project description and features

### Other Documentation
- `backend/` - Backend development docs
- `db/` - Database documentation
- `frontend/` - Frontend development docs
- `tests/` - Testing documentation

## Configuration (config/)

### Docker Configuration
- `docker-compose.yml` - Docker Compose setup
- `Dockerfile` - Docker image definition

## Data (data/)

### Logs (data/logs/)
Application logs.

### Output (data/output/)
Processed audio output files.

### Presets (data/presets/)
Audio processing presets.

### Sessions (data/sessions/)
Session data and state.

## GitHub (.github/)

### Workflows (.github/workflows/)
CI/CD pipeline definitions.

### Copilot Instructions (.github/copilot-instructions.md)
Instructions for GitHub Copilot usage.

## Configuration Files

### Python Project (pyproject.toml)
Modern Python project configuration with build system, dependencies, and tool settings.

### Requirements (requirements.txt)
Production Python dependencies.

### Development Requirements (requirements-dev.txt)
Development and testing dependencies.

### Docker Compose (config/docker-compose.yml)
Multi-container Docker application setup.

### Deployment Scripts (config/)
- `deploy.ps1` - PowerShell deployment script
- `deploy.sh` - Bash deployment script

