# Core Module Specifications

## Overview
The core module provides the fundamental types, exceptions, and interfaces for the audio toolkit.

## Types

### AudioFile
Represents metadata for an audio file.

**Fields:**
- `path: Path` - File system path to the audio file
- `format: str` - Audio format (e.g., 'mp3', 'wav', 'flac')
- `duration: float` - Duration in seconds
- `sample_rate: int` - Sample rate in Hz
- `channels: int` - Number of audio channels
- `bitrate: Optional[int]` - Bitrate in kbps (for compressed formats)

### ProcessingConfig
Configuration for audio processing operations.

**Fields:**
- `output_format: str` - Target output format (default: 'mp3')
- `quality: int` - Quality/bitrate setting (default: 128)
- `normalize: bool` - Whether to normalize audio levels (default: False)
- `remove_silence: bool` - Whether to remove silent sections (default: False)
- `metadata: Optional[Dict[str, Any]]` - Additional metadata to embed

### SplitConfig
Configuration for audio splitting operations.

**Fields:**
- `method: str` - Splitting method ('fixed', 'segments') (default: 'fixed')
- `duration: Optional[float]` - Duration per segment for fixed splitting
- `segments: Optional[List[float]]` - Custom segment boundaries
- `output_prefix: str` - Prefix for output files (default: 'segment')

### ConversionResult
Result of an audio conversion operation.

**Fields:**
- `input_file: AudioFile` - Original audio file
- `output_file: AudioFile` - Converted audio file
- `success: bool` - Whether conversion succeeded
- `error_message: Optional[str]` - Error message if failed
- `processing_time: float` - Time taken for processing

### SplitResult
Result of an audio splitting operation.

**Fields:**
- `input_file: AudioFile` - Original audio file
- `output_files: List[AudioFile]` - List of split segments
- `success: bool` - Whether splitting succeeded
- `error_message: Optional[str]` - Error message if failed
- `processing_time: float` - Time taken for processing

## Exceptions

### AudioToolkitError
Base exception for all audio toolkit errors.

### InvalidAudioFormatError
Raised when an unsupported audio format is encountered.

### AudioProcessingError
Raised when audio processing operations fail.

### FileNotFoundError
Raised when audio files cannot be found.

### ConfigurationError
Raised when configuration is invalid.

### ValidationError
Raised when input validation fails.

## Interfaces

### AudioProcessor
Abstract base class for audio processing components.

**Methods:**
- `process(audio_file: AudioFile, config: ProcessingConfig) -> ConversionResult`

### AudioSplitter
Abstract base class for audio splitting components.

**Methods:**
- `split(audio_file: AudioFile, config: SplitConfig) -> SplitResult`

### AudioValidator
Abstract base class for audio validation components.

**Methods:**
- `validate(audio_file: AudioFile) -> bool`
- `get_validation_errors(audio_file: AudioFile) -> List[str]`

### ProgressReporter
Abstract base class for progress reporting.

**Methods:**
- `start(total_steps: int, description: str = "")`
- `update(current_step: int)`
- `complete()`