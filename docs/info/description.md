# Audio Toolkit

## Description

The Audio Toolkit is a comprehensive Python application for processing and manipulating audio files. It provides a command-line interface for common audio operations including format conversion, audio splitting, and batch processing.

## Features

### Audio Conversion
- Convert between multiple audio formats (MP3, WAV, FLAC, AAC)
- Quality and bitrate control
- Audio normalization
- Silence removal
- Metadata preservation

### Audio Splitting
- Split audio files into fixed-duration segments
- Custom segment boundaries
- Batch processing capabilities
- Configurable output naming

### Batch Processing
- Process multiple files at once
- Directory-based operations
- Recursive file discovery
- Progress reporting

### Quality Assurance
- Input validation
- Error handling and recovery
- Comprehensive logging
- Test coverage

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **Core**: Fundamental types, exceptions, and interfaces
- **Utils**: Utility functions for logging, file operations, and validation
- **Processors**: Audio processing components (converters, splitters)
- **Presentation**: User interfaces (CLI)
- **Tests**: Unit and integration tests

## Technology Stack

- **Python 3.8+**: Core language
- **pydub**: Audio processing library
- **Click**: Command-line interface framework
- **pytest**: Testing framework
- **Docker**: Containerization
- **GitHub Actions**: CI/CD

## Installation

### Requirements
- Python 3.8 or higher
- FFmpeg (for audio processing)

### Setup
```bash
# Clone repository
git clone <repository-url>
cd audio-toolkit

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### Docker
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## Usage

### Convert Audio
```bash
# Convert to MP3 with high quality
audio-toolkit convert input.wav --format mp3 --quality 192

# Convert with normalization
audio-toolkit convert input.wav --normalize --remove-silence
```

### Split Audio
```bash
# Split into 30-second segments
audio-toolkit split input.mp3 --duration 30

# Split with custom output directory
audio-toolkit split input.mp3 --output-dir ./segments --prefix chapter
```

### Batch Processing
```bash
# Process all audio files in directory
find . -name "*.wav" -exec audio-toolkit convert {} --format mp3 \;
```

## Configuration

The application can be configured via:
- Command-line options
- Configuration file (`~/.audio_toolkit/config.json`)
- Environment variables

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality
```bash
# Lint code
flake8 src/

# Format code
black src/
```

### Documentation
```bash
# Generate documentation
sphinx-build docs/ build/docs/
```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation in `docs/`
- Open an issue on GitHub
- Review the test cases for usage examples