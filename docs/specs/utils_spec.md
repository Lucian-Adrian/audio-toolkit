# Utils Module Specifications

## Overview
The utils module provides utility functions for logging, file operations, audio processing, configuration management, progress reporting, and input validation.

## Logger

### setup_logger()
Configures logging for the application.

**Parameters:**
- `name: str` - Logger name (default: 'audio_toolkit')
- `level: int` - Logging level (default: logging.INFO)
- `log_file: Optional[Path]` - Optional log file path
- `console: bool` - Whether to log to console (default: True)

**Returns:** Configured logger instance

## File Operations

### ensure_directory()
Ensures a directory exists, creating it if necessary.

**Parameters:**
- `path: Path` - Directory path to create

### get_audio_files()
Gets all audio files in a directory with specified extensions.

**Parameters:**
- `directory: Path` - Directory to search
- `extensions: Set[str]` - File extensions to include

**Returns:** List of audio file paths

### copy_file(), move_file(), delete_file()
File manipulation utilities with error handling.

## Audio Utils

### load_audio_file()
Loads audio file metadata using pydub.

**Parameters:**
- `file_path: Path` - Path to audio file

**Returns:** AudioFile instance with metadata

### validate_audio_format()
Validates that an audio file format is supported.

**Parameters:**
- `file_path: Path` - Path to audio file
- `supported_formats: set` - Set of supported formats

**Raises:** InvalidAudioFormatError for unsupported formats

### get_audio_duration()
Gets the duration of an audio file.

**Parameters:**
- `file_path: Path` - Path to audio file

**Returns:** Duration in seconds

### extract_audio_segment()
Extracts a segment from an audio file.

**Parameters:**
- `file_path: Path` - Source audio file
- `start_time: float` - Start time in seconds
- `end_time: float` - End time in seconds
- `output_path: Optional[Path]` - Output path (auto-generated if None)

**Returns:** Path to extracted segment

## Configuration

### ConfigManager
Manages application configuration stored in JSON.

**Methods:**
- `load_config()` - Load config from file
- `save_config()` - Save config to file
- `get(key, default)` - Get config value
- `set(key, value)` - Set config value
- `get_processing_config()` - Get ProcessingConfig
- `get_split_config()` - Get SplitConfig

## Progress Reporting

### ConsoleProgressReporter
Console-based progress reporter with percentage display.

### SilentProgressReporter
Progress reporter that produces no output.

### get_progress_reporter()
Factory function for progress reporters.

**Parameters:**
- `use_console: bool` - Whether to use console reporter

**Returns:** ProgressReporter instance

## Validators

### AudioFileValidator
Validates audio files for processing.

**Methods:**
- `validate(audio_file)` - Validate file
- `get_validation_errors(audio_file)` - Get list of validation errors

### validate_output_directory()
Validates and creates output directory.

### validate_positive_number()
Validates that a number is positive.

### validate_file_list()
Filters list of paths to valid files.