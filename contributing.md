# Contributing to Audio Toolkit

Thank you for your interest in contributing! This guide will help you get started.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Creating Plugins](#creating-plugins)

## Development Setup

### Prerequisites

- Python 3.13 or higher
- FFmpeg installed and in PATH
- Git

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/Lucian-Adrian/audio-toolkit.git
cd audio-toolkit

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"

# Or install from requirements files
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Verify Installation

```bash
# Run tests
pytest

# Check CLI works
audiotoolkit --help
```

## Project Structure

```
audio-toolkit/
├── src/
│   ├── core/           # Interfaces, types, exceptions
│   ├── processors/     # Audio processors
│   ├── orchestration/  # Pipeline, session, plugin management
│   ├── presentation/   # CLI and wizard
│   └── utils/          # Utilities
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── fixtures/       # Test data
└── docs/               # Documentation
```

See [docs/file-structure.md](docs/file-structure.md) for complete details.

## Code Style

### Python Style

We follow PEP 8 with these tools:

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Naming Conventions

- **Files**: snake_case (`plugin_manager.py`)
- **Classes**: PascalCase (`PluginManager`)
- **Functions/Methods**: snake_case (`discover_plugins`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT`)
- **Processor names**: kebab-case (`splitter-fixed`)

### Docstrings

Use Google-style docstrings:

```python
def process_file(input_path: Path, output_dir: Path) -> ProcessResult:
    """
    Process a single audio file.
    
    Args:
        input_path: Path to the input audio file.
        output_dir: Directory for output files.
        
    Returns:
        ProcessResult containing success status and output paths.
        
    Raises:
        AudioProcessingError: If processing fails.
    """
```

### Type Hints

Use type hints for all public functions:

```python
from pathlib import Path
from typing import List, Optional

def find_audio_files(
    directory: Path,
    recursive: bool = True,
    extensions: Optional[List[str]] = None,
) -> List[Path]:
    ...
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_plugin_manager.py -v

# Run tests matching pattern
pytest -k "test_discover" -v

# Run only fast tests
pytest -m "not slow"
```

### Writing Tests

```python
# tests/unit/test_my_feature.py
import pytest
from pathlib import Path


class TestMyFeature:
    """Tests for MyFeature class."""
    
    def test_basic_functionality(self):
        """Test that basic functionality works."""
        result = my_function()
        assert result == expected
    
    def test_edge_case(self):
        """Test edge case handling."""
        with pytest.raises(ValueError):
            my_function(invalid_input)
    
    @pytest.fixture
    def sample_data(self, tmp_path):
        """Create sample test data."""
        file_path = tmp_path / "test.mp3"
        file_path.write_bytes(b"fake audio")
        return file_path
    
    def test_with_fixture(self, sample_data):
        """Test using fixture data."""
        result = process_file(sample_data)
        assert result.success
```

### Test Organization

- **Unit tests**: `tests/unit/test_<module>.py`
- **Integration tests**: `tests/integration/test_<feature>.py`
- **Fixtures**: `tests/conftest.py` and `tests/fixtures/`

### Coverage Goals

- Maintain overall coverage above 80%
- New code should have 90%+ coverage
- Critical paths (processors, session management) should have 95%+ coverage

## Pull Request Process

### Before Submitting

1. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes**
   - Follow code style guidelines
   - Add/update tests
   - Update documentation

3. **Run quality checks**
   ```bash
   # Format
   black src/ tests/
   
   # Lint
   ruff check src/ tests/
   
   # Type check
   mypy src/
   
   # Test
   pytest --cov=src
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "feat: add volume normalization processor"
   ```
   
   Use conventional commits:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation
   - `test:` - Tests
   - `refactor:` - Code refactoring
   - `chore:` - Maintenance

### Submitting

1. Push your branch:
   ```bash
   git push origin feature/my-feature
   ```

2. Open a Pull Request with:
   - Clear title describing the change
   - Description of what and why
   - Link to related issues
   - Screenshots if UI changes

3. Address review feedback

4. Squash commits if requested

### Review Criteria

- [ ] Tests pass
- [ ] Coverage maintained or improved
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)

## Creating Plugins

To create a new audio processor plugin:

1. Implement the `AudioProcessor` interface
2. Register via `audiotoolkit.plugins` entry point
3. See [docs/plugins/creating-plugins.md](docs/plugins/creating-plugins.md) for complete guide

### Example

```python
from src.core.interfaces import AudioProcessor
from src.core.types import ProcessorCategory, ParameterSpec, ProcessResult

class MyProcessor(AudioProcessor):
    @property
    def name(self) -> str:
        return "my-processor"
    
    # ... implement other required properties/methods
```

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: Email security@example.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

