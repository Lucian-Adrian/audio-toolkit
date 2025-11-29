"""Configuration management for the audio toolkit."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from ..core.types import ProcessingConfig, SplitConfig
from ..core.exceptions import ConfigurationError
from .logger import logger


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path.home() / ".audio_toolkit" / "config.json"
        self._config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
                logger.debug(f"Loaded config from {self.config_file}")
            else:
                self._config = self._get_default_config()
                self.save_config()
        except Exception as e:
            logger.warning(f"Failed to load config, using defaults: {e}")
            self._config = self._get_default_config()

    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            logger.debug(f"Saved config to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise ConfigurationError(f"Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
        self.save_config()

    def get_processing_config(self) -> ProcessingConfig:
        """Get processing configuration."""
        proc_config = self._config.get('processing', {})
        return ProcessingConfig(
            output_format=proc_config.get('output_format', 'mp3'),
            quality=proc_config.get('quality', 128),
            normalize=proc_config.get('normalize', False),
            remove_silence=proc_config.get('remove_silence', False),
            metadata=proc_config.get('metadata')
        )

    def get_split_config(self) -> SplitConfig:
        """Get split configuration."""
        split_config = self._config.get('split', {})
        return SplitConfig(
            method=split_config.get('method', 'fixed'),
            duration=split_config.get('duration'),
            segments=split_config.get('segments'),
            output_prefix=split_config.get('output_prefix', 'segment')
        )

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'processing': {
                'output_format': 'mp3',
                'quality': 128,
                'normalize': False,
                'remove_silence': False
            },
            'split': {
                'method': 'fixed',
                'output_prefix': 'segment'
            },
            'logging': {
                'level': 'INFO',
                'file': None
            }
        }


# Global config instance
config_manager = ConfigManager()