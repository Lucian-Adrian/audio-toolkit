# 🎵 Audio Toolkit

A comprehensive CLI toolkit for batch audio processing with session management, crash recovery, and plugin support.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-622%20passed-green.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen.svg)]()

## Features

- 🔪 **Audio Splitting** - Split audio files by fixed duration, silence detection, or timestamp files
- 🔄 **Format Conversion** - Convert between MP3, WAV, FLAC, OGG, AAC, M4A with quality options
- 📊 **Audio Analysis** - Visualizations, statistics, voice activity detection, and transcription
- 🎙️ **Voice Enhancement** - Noise reduction, dynamics processing, and automatic silence trimming
- 📊 **Session Management** - Track processing progress with crash recovery support
- 🔧 **Pipeline Engine** - Define multi-step workflows in YAML
- 🧙 **Interactive Wizard** - Guided configuration for all operations
- 🔌 **Plugin System** - Extend functionality with third-party processors
- 💾 **Preset System** - Save and reuse configurations

## Installation

### From PyPI (Recommended)

```bash
pip install audio-toolkit
```

### From Source

```bash
git clone https://github.com/Lucian-Adrian/audio-toolkit.git
cd audio-toolkit
pip install -e .
```

### Dependencies

Audio Toolkit requires FFmpeg for audio processing:

- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg` or equivalent

## Quick Start

### Interactive Wizard

Launch the interactive wizard for guided configuration:

```bash
audiotoolkit
# or explicitly:
audiotoolkit --wizard
```

### Command Line

#### Split Audio Files

```bash
# Split into 30-second segments
audiotoolkit split fixed --duration 30 --input ./audio --output ./output

# Split a single file
audiotoolkit split fixed --duration 60 --input podcast.mp3 --output ./segments
```

#### Convert Audio Formats

```bash
# Convert to MP3
audiotoolkit convert files --format mp3 --input ./audio --output ./converted

# Convert with options
audiotoolkit convert files --format wav --sample-rate 44100 --channels 2 --input ./audio
```

#### Manage Plugins

```bash
# List available processors
audiotoolkit plugins list

# Show processor details
audiotoolkit plugins info splitter-fixed

# Disable a processor
audiotoolkit plugins disable converter
```

#### Run Pipelines

```bash
# Run a pipeline from YAML
audiotoolkit pipeline run --config ./my-pipeline.yaml

# Validate pipeline before running
audiotoolkit pipeline validate --config ./my-pipeline.yaml

# Dry run to see execution plan
audiotoolkit pipeline run --config ./my-pipeline.yaml --dry-run
```

#### Manage Sessions

```bash
# List recent sessions
audiotoolkit sessions list

# Resume an incomplete session
audiotoolkit sessions resume

# Clean old sessions
audiotoolkit sessions clean --older-than 7
```

#### Analyze Audio

```bash
# Generate visualizations (waveform, spectrogram)
audiotoolkit analyze visualize audio.wav --type combined

# Get audio statistics (RMS, peak, silence ratio, VAD)
audiotoolkit analyze stats audio.wav --save

# Transcribe audio (requires openai-whisper)
audiotoolkit analyze transcribe podcast.mp3 --model base --format srt
```

#### Voice Enhancement

```bash
# Reduce background noise
audiotoolkit voice denoise noisy.wav --reduction 15

# Apply dynamics processing (compression + EQ)
audiotoolkit voice dynamics voice.mp3 --threshold -18 --ratio 4 --eq-mid 2

# Trim silence from audio
audiotoolkit voice trim recording.wav --mode all

# Apply complete voice enhancement chain
audiotoolkit voice enhance podcast.wav --preset podcast
```

### Using Presets

```bash
# Run with a saved preset
audiotoolkit --preset my-split-config

# Presets are saved via the wizard
```

## Pipeline Configuration

Create YAML files to define multi-step workflows:

```yaml
# podcast-prep.yaml
name: "podcast-prep"
description: "Prepare podcast episodes"
version: "1.0"

settings:
  checkpoint_interval: 50
  continue_on_error: false
  output_dir: "./output"

input:
  path: "./raw-episodes"
  recursive: true
  formats: ["mp3", "wav", "m4a"]

steps:
  - name: normalize
    processor: converter
    params:
      output_format: wav
      normalize_audio: true

  - name: split-segments
    processor: splitter-fixed
    params:
      duration_ms: 300000  # 5 minutes
      output_format: mp3
```

## Available Processors

| Processor | Category | Description |
|-----------|----------|-------------|
| `splitter-fixed` | manipulation | Split audio into fixed-duration segments |
| `converter` | manipulation | Convert audio between formats with optional processing |
| `visualizer` | analysis | Generate waveform and spectrogram visualizations |
| `statistics` | analysis | Analyze audio for RMS, peak, dynamic range, silence ratio |
| `transcriber` | analysis | Transcribe audio using OpenAI Whisper |
| `noise_reduce` | voice | Reduce background noise using spectral subtraction |
| `dynamics` | voice | Apply compression and 3-band EQ |
| `trimmer` | voice | Automatically trim silence from audio |

Use `audiotoolkit plugins list --verbose` to see all parameters.

## Creating Plugins

Audio Toolkit supports third-party plugins via Python entry points. See the [Plugin Development Guide](docs/plugins/creating-plugins.md) for details.

### Quick Example

```python
from src.core.interfaces import AudioProcessor
from src.core.types import ParameterSpec, ProcessorCategory, ProcessResult

class MyProcessor(AudioProcessor):
    @property
    def name(self) -> str:
        return "my-processor"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "My custom audio processor"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.MANIPULATION
    
    @property
    def parameters(self) -> list[ParameterSpec]:
        return []
    
    def process(self, input_path, output_dir, **kwargs) -> ProcessResult:
        # Your processing logic here
        pass
```

Register in `pyproject.toml`:

```toml
[project.entry-points."audiotoolkit.plugins"]
my-processor = "my_package.processor:MyProcessor"
```

## Project Structure

```
audio-toolkit/
├── src/
│   ├── core/           # Interfaces, types, exceptions
│   ├── processors/     # Audio processors (splitter, converter)
│   ├── orchestration/  # Pipeline, session, plugin management
│   ├── presentation/   # CLI and wizard interfaces
│   └── utils/          # Utilities (audio, logging, config)
├── tests/              # Unit and integration tests
├── docs/               # Documentation
├── config/             # Docker and editor config
└── data/               # Runtime data (logs, output, presets)
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/Lucian-Adrian/audio-toolkit.git
cd audio-toolkit

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_plugin_manager.py -v
```

### Code Quality

```bash
# Type checking
mypy src/

# Linting
ruff check src/

# Format code
black src/
```

## Contributing

See [CONTRIBUTING.md](contributing.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](changelog.md) for version history.
