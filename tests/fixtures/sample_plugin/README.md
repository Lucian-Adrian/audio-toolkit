# Sample Audio Toolkit Plugin

This is an example plugin demonstrating how to create third-party processors for Audio Toolkit.

## Installation

```bash
pip install -e tests/fixtures/sample_plugin/
```

## Usage

After installation, the plugin will be automatically discovered:

```bash
# List all plugins (should include echo-test)
audiotoolkit plugins list

# Show plugin details
audiotoolkit plugins info echo-test
```

## Creating Your Own Plugin

1. Create a class that inherits from `AudioProcessor`
2. Implement all required properties and methods
3. Register via entry_points in `pyproject.toml`

### Example

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
    def parameters(self) -> List[ParameterSpec]:
        return []
    
    def process(self, input_path, output_dir, **kwargs) -> ProcessResult:
        # Your processing logic here
        pass
```

### pyproject.toml

```toml
[project.entry-points."audiotoolkit.plugins"]
my-processor = "my_package.processor:MyProcessor"
```
