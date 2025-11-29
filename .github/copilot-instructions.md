# GitHub Copilot Instructions for Audio Toolkit

## Project Overview
The Audio Toolkit is a Python application for processing audio files. It provides command-line tools for converting audio formats, splitting audio files, and batch processing operations.

## Architecture
- **Modular Design**: Core types/exceptions, utilities, processors, and presentation layers
- **CLI Interface**: Click-based command-line interface
- **Audio Processing**: Uses pydub for audio manipulation
- **Configuration**: JSON-based configuration management
- **Testing**: pytest with unit and integration tests

## Key Components

### Core Module
- `types.py`: Data classes for AudioFile, ProcessingConfig, etc.
- `exceptions.py`: Custom exception hierarchy
- `interfaces.py`: Abstract base classes for processors

### Utils Module
- `logger.py`: Logging setup
- `file_ops.py`: File system operations
- `audio.py`: Audio file utilities
- `config.py`: Configuration management
- `progress.py`: Progress reporting
- `validators.py`: Input validation

### Processors Module
- `converter.py`: Audio format conversion
- `splitter/`: Audio splitting (fixed duration, etc.)
- Registry pattern for processor discovery

### CLI Module
- `convert` command: Format conversion with options
- `split` command: Audio splitting with configuration

## Development Guidelines

### Code Style
- Follow PEP 8 conventions
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Use descriptive variable names

### Error Handling
- Use custom exceptions from `core.exceptions`
- Provide meaningful error messages
- Log errors appropriately
- Handle edge cases gracefully

### Testing
- Write unit tests for all new functionality
- Include integration tests for workflows
- Use fixtures for test data
- Aim for high test coverage

### Documentation
- Update specifications in `docs/specs/` for new features
- Maintain file structure documentation
- Keep README and descriptions current

## Common Patterns

### Creating a New Processor
1. Implement the appropriate interface (`AudioProcessor` or `AudioSplitter`)
2. Register in the processor registry
3. Add configuration types if needed
4. Write comprehensive tests
5. Update CLI commands

### Adding CLI Commands
1. Create command function in appropriate CLI module
2. Add to main CLI group
3. Handle argument validation
4. Provide progress reporting
5. Include error handling

### Configuration Management
1. Add new settings to `ConfigManager`
2. Update default configuration
3. Provide CLI options for overrides
4. Document configuration options

## File Organization
- Keep related functionality together
- Use clear module boundaries
- Import from parent packages with relative imports
- Maintain consistent directory structure

## Audio Processing Notes
- Always validate input files before processing
- Use temporary files for intermediate results
- Preserve metadata when possible
- Handle different audio formats appropriately
- Consider memory usage for large files

## Git Workflow
- Make granular commits for logical changes
- Use descriptive commit messages
- Keep branches focused on single features
- Write clear pull request descriptions

## Quality Assurance
- Run tests before committing
- Check code with linters
- Validate audio processing results
- Test edge cases and error conditions
