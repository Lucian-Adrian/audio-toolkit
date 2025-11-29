"""Configuration management utilities."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.exceptions import ConfigError, InvalidYAMLError
from .logger import get_logger

logger = get_logger(__name__)

# Default configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    "output_dir": "data/output",
    "log_dir": "data/logs",
    "sessions_dir": "data/sessions",
    "default_format": "mp3",
    "default_bitrate": "192k",
    "checkpoint_interval": 10,
}


def load_json_config(path: Path) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        path: Path to JSON config file
        
    Returns:
        Configuration dictionary
        
    Raises:
        ConfigError: If file cannot be read
        InvalidYAMLError: If JSON is invalid
    """
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise InvalidYAMLError(f"Invalid JSON in {path}: {e}")
    except OSError as e:
        raise ConfigError(f"Cannot read config file {path}: {e}")


def save_json_config(config: Dict[str, Any], path: Path) -> None:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        path: Path to save to
        
    Raises:
        ConfigError: If file cannot be written
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        logger.debug(f"Saved config to {path}")
    except OSError as e:
        raise ConfigError(f"Cannot write config file {path}: {e}")


def get_config_value(
    config: Dict[str, Any],
    key: str,
    default: Any = None,
) -> Any:
    """
    Get a configuration value with dot notation support.
    
    Args:
        config: Configuration dictionary
        key: Key in dot notation (e.g., "output.format")
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    keys = key.split(".")
    value = config
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries.
    
    Override values take precedence. Nested dicts are merged recursively.
    
    Args:
        base: Base configuration
        override: Override configuration
        
    Returns:
        Merged configuration
    """
    result = base.copy()
    
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to config file (optional)
        """
        self._config = DEFAULT_CONFIG.copy()
        self._config_path = config_path
        
        if config_path and config_path.exists():
            self.load(config_path)
    
    def load(self, path: Path) -> None:
        """Load configuration from file."""
        loaded = load_json_config(path)
        self._config = merge_configs(self._config, loaded)
        self._config_path = path
        logger.info(f"Loaded config from {path}")
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        path = path or self._config_path
        if not path:
            raise ConfigError("No config path specified")
        save_json_config(self._config, path)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return get_config_value(self._config, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        keys = key.split(".")
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._config.copy()
