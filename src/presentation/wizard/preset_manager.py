"""Preset manager for saving and loading wizard configurations.

Presets allow users to save their frequently-used configurations
and quickly reuse them without going through the full wizard flow.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...core.exceptions import ConfigError
from ...utils.logger import get_logger

logger = get_logger(__name__)


class PresetConfig(BaseModel):
    """Schema for a saved preset configuration."""
    
    model_config = ConfigDict(extra="allow")
    
    name: str = Field(..., min_length=1, max_length=100)
    operation: str = Field(..., description="Operation type: split, convert, etc.")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = Field(default=None, max_length=500)
    config: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate preset name is safe for filesystem."""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            v = v.replace(char, "_")
        return v.strip()


class PresetManager:
    """Manages user presets for wizard configurations.
    
    Presets are stored as YAML files in the user's home directory
    or a custom location.
    
    Attributes:
        preset_dir: Directory where presets are stored
    """
    
    DEFAULT_DIR = Path.home() / ".audiotoolkit" / "presets"
    
    def __init__(self, preset_dir: Optional[Path] = None):
        """Initialize the preset manager.
        
        Args:
            preset_dir: Custom directory for presets (optional)
        """
        self.preset_dir = preset_dir or self.DEFAULT_DIR
        self._ensure_preset_dir()
    
    def _ensure_preset_dir(self) -> None:
        """Ensure the preset directory exists."""
        try:
            self.preset_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Could not create preset directory: {e}")
    
    def _get_preset_path(self, name: str) -> Path:
        """Get the file path for a preset.
        
        Args:
            name: Preset name
            
        Returns:
            Path to the preset file
        """
        # Sanitize name for filesystem
        safe_name = "".join(
            c if c.isalnum() or c in "-_" else "_"
            for c in name
        )
        return self.preset_dir / f"{safe_name}.yaml"
    
    def save_preset(
        self,
        name: str,
        operation: str,
        config: Dict[str, Any],
        description: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        """Save a configuration as a preset.
        
        Args:
            name: Preset name (used as identifier)
            operation: Operation type (split, convert, etc.)
            config: Configuration dictionary
            description: Optional description
            overwrite: Whether to overwrite existing preset
            
        Returns:
            Path to the saved preset file
            
        Raises:
            ConfigError: If preset exists and overwrite=False
            ConfigError: If preset cannot be saved
        """
        preset_path = self._get_preset_path(name)
        
        if preset_path.exists() and not overwrite:
            raise ConfigError(
                f"Preset '{name}' already exists. Use overwrite=True to replace."
            )
        
        # Convert Path objects to strings for YAML serialization
        serializable_config = self._serialize_config(config)
        
        preset = PresetConfig(
            name=name,
            operation=operation,
            config=serializable_config,
            description=description,
            created_at=datetime.now() if not preset_path.exists() else self._get_existing_created_at(preset_path),
            updated_at=datetime.now(),
        )
        
        try:
            with open(preset_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    preset.model_dump(mode="json"),
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
            logger.info(f"Saved preset '{name}' to {preset_path}")
            return preset_path
        except OSError as e:
            raise ConfigError(f"Failed to save preset: {e}")
    
    def _get_existing_created_at(self, path: Path) -> datetime:
        """Get created_at from existing preset file."""
        try:
            existing = self.load_preset(path.stem)
            return existing.get("created_at", datetime.now())
        except Exception:
            return datetime.now()
    
    def _serialize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert config values to YAML-serializable types.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Serializable dictionary
        """
        result = {}
        for key, value in config.items():
            if isinstance(value, Path):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = self._serialize_config(value)
            elif isinstance(value, (list, tuple)):
                result[key] = [
                    str(v) if isinstance(v, Path) else v
                    for v in value
                ]
            else:
                result[key] = value
        return result
    
    def load_preset(self, name: str) -> Dict[str, Any]:
        """Load a preset by name.
        
        Args:
            name: Preset name
            
        Returns:
            Preset configuration dictionary
            
        Raises:
            ConfigError: If preset not found or invalid
        """
        preset_path = self._get_preset_path(name)
        
        if not preset_path.exists():
            raise ConfigError(f"Preset '{name}' not found")
        
        try:
            with open(preset_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                raise ConfigError(f"Invalid preset format in '{name}'")
            
            logger.info(f"Loaded preset '{name}' from {preset_path}")
            return data
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in preset '{name}': {e}")
        except OSError as e:
            raise ConfigError(f"Failed to read preset '{name}': {e}")
    
    def list_presets(
        self,
        operation: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all saved presets.
        
        Args:
            operation: Filter by operation type (optional)
            
        Returns:
            List of preset metadata dictionaries
        """
        presets = []
        
        if not self.preset_dir.exists():
            return presets
        
        for path in sorted(self.preset_dir.glob("*.yaml")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                
                if isinstance(data, dict):
                    # Filter by operation if specified
                    if operation and data.get("operation") != operation:
                        continue
                    
                    presets.append({
                        "name": data.get("name", path.stem),
                        "operation": data.get("operation", "unknown"),
                        "description": data.get("description"),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                        "path": path,
                    })
            except Exception as e:
                logger.warning(f"Skipping invalid preset {path}: {e}")
        
        return presets
    
    def delete_preset(self, name: str) -> bool:
        """Delete a preset.
        
        Args:
            name: Preset name
            
        Returns:
            True if deleted, False if not found
        """
        preset_path = self._get_preset_path(name)
        
        if not preset_path.exists():
            return False
        
        try:
            preset_path.unlink()
            logger.info(f"Deleted preset '{name}'")
            return True
        except OSError as e:
            logger.error(f"Failed to delete preset '{name}': {e}")
            return False
    
    def preset_exists(self, name: str) -> bool:
        """Check if a preset exists.
        
        Args:
            name: Preset name
            
        Returns:
            True if preset exists
        """
        return self._get_preset_path(name).exists()
    
    def get_preset_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a preset without loading full config.
        
        Args:
            name: Preset name
            
        Returns:
            Preset metadata or None if not found
        """
        preset_path = self._get_preset_path(name)
        
        if not preset_path.exists():
            return None
        
        try:
            with open(preset_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            return {
                "name": data.get("name", name),
                "operation": data.get("operation"),
                "description": data.get("description"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "config_keys": list(data.get("config", {}).keys()),
            }
        except Exception:
            return None
    
    def export_preset(self, name: str, output_path: Path) -> Path:
        """Export a preset to a specified location.
        
        Args:
            name: Preset name
            output_path: Destination path
            
        Returns:
            Path to exported file
            
        Raises:
            ConfigError: If preset not found or export fails
        """
        data = self.load_preset(name)
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, default_flow_style=False)
            return output_path
        except OSError as e:
            raise ConfigError(f"Failed to export preset: {e}")
    
    def import_preset(
        self,
        source_path: Path,
        name: Optional[str] = None,
        overwrite: bool = False,
    ) -> str:
        """Import a preset from a file.
        
        Args:
            source_path: Path to preset file
            name: Custom name (optional, uses file name by default)
            overwrite: Whether to overwrite existing
            
        Returns:
            Name of imported preset
            
        Raises:
            ConfigError: If import fails
        """
        if not source_path.exists():
            raise ConfigError(f"Source file not found: {source_path}")
        
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            preset_name = name or data.get("name") or source_path.stem
            
            self.save_preset(
                name=preset_name,
                operation=data.get("operation", "unknown"),
                config=data.get("config", {}),
                description=data.get("description"),
                overwrite=overwrite,
            )
            
            return preset_name
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in source file: {e}")
