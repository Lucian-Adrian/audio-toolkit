# Processors Module Specifications

## Overview
The processors module provides audio processing components including converters and splitters, organized in a registry pattern.

## Registry

### ProcessorRegistry
Central registry for audio processors and splitters.

**Methods:**
- `register_processor(name, processor_class)` - Register processor
- `register_splitter(name, splitter_class)` - Register splitter
- `get_processor(name)` - Get processor class
- `get_splitter(name)` - Get splitter class
- `list_processors()` - List available processors
- `list_splitters()` - List available splitters

## Converter

### AudioConverter
Converts audio files between formats using pydub.

**Features:**
- Format conversion (MP3, WAV, FLAC, AAC)
- Quality/bitrate control
- Audio normalization
- Silence removal

**Supported formats:** mp3, wav, flac, aac

**Process method:**
- Takes AudioFile and ProcessingConfig
- Returns ConversionResult

## Splitter

### BaseSplitter
Abstract base class for audio splitters.

**Methods:**
- `_get_segments()` - Abstract method to define segments
- `_get_output_path()` - Generate output paths

### FixedDurationSplitter
Splits audio into fixed-duration segments.

**Configuration:**
- `duration: float` - Seconds per segment

**Behavior:**
- Divides audio into equal segments
- Last segment may be shorter
- Outputs segments as separate files

## Usage Examples

### Converting Audio
```python
converter = AudioConverter()
config = ProcessingConfig(output_format='mp3', quality=192, normalize=True)
result = converter.process(audio_file, config)
```

### Splitting Audio
```python
splitter = FixedDurationSplitter()
config = SplitConfig(duration=30.0)  # 30-second segments
result = splitter.split(audio_file, config)
```

### Using Registry
```python
from src.processors import registry

converter_class = registry.get_processor('converter')
converter = converter_class()
```