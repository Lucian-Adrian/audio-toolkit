# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-XX

### Added

#### Core Foundation (Phase 1)
- Core interfaces: `AudioProcessor`, `SessionStore`, `ProgressReporter`
- Core types: `ProcessorCategory`, `ParameterSpec`, `ProcessResult`, `Session`, `FileRecord`
- Custom exceptions: `AudioProcessingError`, `InvalidAudioFormatError`, `ProcessorNotFoundError`
- Utility modules: logging, file operations, audio helpers, configuration, validators

#### Audio Processors (Phase 2)
- `FixedDurationSplitter` - Split audio into fixed-duration segments
- `Converter` - Convert between audio formats (MP3, WAV, FLAC, OGG, AAC, M4A)
- Processor registry with factory pattern
- Support for sample rate, channels, and bitrate configuration

#### Session Management (Phase 3)
- `SessionManager` - Track batch processing state
- `JsonSessionStore` - Persistent session storage with JSON
- Crash recovery - Resume interrupted sessions
- Progress tracking with file-level granularity
- Session cleanup for old sessions

#### Pipeline Engine (Phase 4)
- `PipelineConfig` - Pydantic models for YAML pipeline definitions
- `PipelineEngine` - Multi-step workflow execution
- Pipeline validation before execution
- Dry-run mode for execution preview
- Step chaining - output of one step feeds next
- Checkpointing during execution
- Error handling with `continue_on_error` option

#### Interactive Wizard (Phase 5)
- Main menu with InquirerPy
- Split operation wizard with guided configuration
- Convert operation wizard with format selection
- Preset system - Save and load configurations
- Rich console output with progress bars

#### Plugin System (Phase 6)
- `PluginManager` - Entry point-based plugin discovery
- CLI commands: `plugins list`, `plugins info`, `plugins disable`, `plugins enable`
- Plugin filtering by category
- Plugin disable/enable persistence
- Sample plugin for testing and documentation

#### Advanced Processors (Phase 7)
- `AudioVisualizer` - Generate waveform and spectrogram visualizations
- `AudioStatistics` - Analyze audio for RMS, peak, dynamic range, silence ratio, VAD
- `NoiseReducer` - Reduce background noise using spectral subtraction
- `DynamicsProcessor` - Apply compression and 3-band EQ
- `AudioTrimmer` - Automatically trim silence from start/end or throughout
- `AudioTranscriber` - Transcribe audio using OpenAI Whisper (txt, json, srt, vtt)
- CLI commands: `analyze visualize`, `analyze stats`, `analyze transcribe`
- CLI commands: `voice denoise`, `voice dynamics`, `voice trim`, `voice enhance`
- Voice enhancement presets (podcast, voice, music)

#### Polish & Release (Phase 8)
- 80% code coverage with 622 unit and integration tests
- Comprehensive test suites for all processors and CLI commands
- Built and tested wheel package (audio_toolkit-1.0.0-py3-none-any.whl)
- Updated documentation (README, file structure, contribution guide)

#### CLI Interface
- Typer-based CLI with subcommands
- `split fixed` - Fixed duration splitting
- `convert files` - Format conversion
- `pipeline run` - Execute pipelines
- `pipeline validate` - Validate pipeline configs
- `sessions list/resume/clean` - Session management
- `plugins list/info/disable/enable/discover` - Plugin management
- `--wizard` flag for interactive mode
- `--preset` flag for saved configurations

#### Documentation
- Comprehensive README with usage examples
- Plugin development guide
- File structure documentation
- Contributing guidelines

### Changed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- Input validation for all file paths
- Safe file operations with proper error handling

## [Unreleased]

### Added
- (Future features will be listed here)

### Changed

### Fixed
