"""Unit tests for configuration utilities."""

import pytest
import json
from pathlib import Path

from src.utils.config import (
    load_json_config,
    save_json_config,
    get_config_value,
    merge_configs,
    ConfigManager,
    DEFAULT_CONFIG,
)
from src.core.exceptions import ConfigError, InvalidYAMLError


class TestLoadJsonConfig:
    """Tests for load_json_config function."""
    
    def test_load_json_config_success(self, temp_dir):
        """Test loading valid JSON config."""
        config_path = temp_dir / "config.json"
        config_data = {"key": "value", "nested": {"inner": 123}}
        config_path.write_text(json.dumps(config_data))
        
        result = load_json_config(config_path)
        
        assert result == config_data
    
    def test_load_json_config_not_found(self, temp_dir):
        """Test loading nonexistent config raises error."""
        config_path = temp_dir / "nonexistent.json"
        
        with pytest.raises(ConfigError) as exc_info:
            load_json_config(config_path)
        
        assert "not found" in str(exc_info.value)
    
    def test_load_json_config_invalid_json(self, temp_dir):
        """Test loading invalid JSON raises error."""
        config_path = temp_dir / "invalid.json"
        config_path.write_text("{invalid json")
        
        with pytest.raises(InvalidYAMLError) as exc_info:
            load_json_config(config_path)
        
        assert "Invalid JSON" in str(exc_info.value)


class TestSaveJsonConfig:
    """Tests for save_json_config function."""
    
    def test_save_json_config_success(self, temp_dir):
        """Test saving JSON config."""
        config_path = temp_dir / "output.json"
        config_data = {"key": "value", "number": 42}
        
        save_json_config(config_data, config_path)
        
        assert config_path.exists()
        loaded = json.loads(config_path.read_text())
        assert loaded == config_data
    
    def test_save_json_config_creates_parents(self, temp_dir):
        """Test that parent directories are created."""
        config_path = temp_dir / "nested" / "deep" / "config.json"
        config_data = {"key": "value"}
        
        save_json_config(config_data, config_path)
        
        assert config_path.exists()


class TestGetConfigValue:
    """Tests for get_config_value function."""
    
    def test_get_config_value_simple(self):
        """Test getting simple value."""
        config = {"key": "value"}
        
        result = get_config_value(config, "key")
        
        assert result == "value"
    
    def test_get_config_value_nested(self):
        """Test getting nested value with dot notation."""
        config = {"level1": {"level2": {"level3": "deep_value"}}}
        
        result = get_config_value(config, "level1.level2.level3")
        
        assert result == "deep_value"
    
    def test_get_config_value_not_found(self):
        """Test getting nonexistent key returns default."""
        config = {"key": "value"}
        
        result = get_config_value(config, "nonexistent", default="default")
        
        assert result == "default"
    
    def test_get_config_value_partial_path_not_found(self):
        """Test getting partially valid path returns default."""
        config = {"level1": {"level2": "value"}}
        
        result = get_config_value(config, "level1.nonexistent.deep", default="default")
        
        assert result == "default"


class TestMergeConfigs:
    """Tests for merge_configs function."""
    
    def test_merge_configs_simple(self):
        """Test merging simple configs."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        
        result = merge_configs(base, override)
        
        assert result == {"a": 1, "b": 3, "c": 4}
    
    def test_merge_configs_nested(self):
        """Test merging nested configs recursively."""
        base = {"level1": {"a": 1, "b": 2}}
        override = {"level1": {"b": 3, "c": 4}}
        
        result = merge_configs(base, override)
        
        assert result == {"level1": {"a": 1, "b": 3, "c": 4}}
    
    def test_merge_configs_override_replaces_non_dict(self):
        """Test override replaces non-dict value."""
        base = {"key": "string"}
        override = {"key": {"nested": "value"}}
        
        result = merge_configs(base, override)
        
        assert result == {"key": {"nested": "value"}}


class TestConfigManager:
    """Tests for ConfigManager class."""
    
    def test_config_manager_init_defaults(self):
        """Test ConfigManager initializes with defaults."""
        manager = ConfigManager()
        
        assert manager.config == DEFAULT_CONFIG
    
    def test_config_manager_init_with_file(self, temp_dir):
        """Test ConfigManager loads from file on init."""
        config_path = temp_dir / "config.json"
        config_data = {"custom_key": "custom_value"}
        config_path.write_text(json.dumps(config_data))
        
        manager = ConfigManager(config_path)
        
        # Should have both defaults and custom value
        assert manager.get("custom_key") == "custom_value"
        assert manager.get("output_dir") == DEFAULT_CONFIG["output_dir"]
    
    def test_config_manager_load(self, temp_dir):
        """Test ConfigManager.load method."""
        manager = ConfigManager()
        config_path = temp_dir / "config.json"
        config_data = {"loaded_key": "loaded_value"}
        config_path.write_text(json.dumps(config_data))
        
        manager.load(config_path)
        
        assert manager.get("loaded_key") == "loaded_value"
    
    def test_config_manager_save(self, temp_dir):
        """Test ConfigManager.save method."""
        config_path = temp_dir / "config.json"
        manager = ConfigManager()
        manager.set("custom", "value")
        
        manager.save(config_path)
        
        assert config_path.exists()
        loaded = json.loads(config_path.read_text())
        assert loaded["custom"] == "value"
    
    def test_config_manager_save_no_path_error(self):
        """Test ConfigManager.save raises error without path."""
        manager = ConfigManager()
        
        with pytest.raises(ConfigError) as exc_info:
            manager.save()
        
        assert "No config path" in str(exc_info.value)
    
    def test_config_manager_get(self):
        """Test ConfigManager.get method."""
        manager = ConfigManager()
        
        result = manager.get("output_dir")
        
        assert result == DEFAULT_CONFIG["output_dir"]
    
    def test_config_manager_get_default(self):
        """Test ConfigManager.get with default value."""
        manager = ConfigManager()
        
        result = manager.get("nonexistent", "default")
        
        assert result == "default"
    
    def test_config_manager_set(self):
        """Test ConfigManager.set method."""
        manager = ConfigManager()
        
        manager.set("new_key", "new_value")
        
        assert manager.get("new_key") == "new_value"
    
    def test_config_manager_set_nested(self):
        """Test ConfigManager.set with nested key."""
        manager = ConfigManager()
        
        manager.set("level1.level2.key", "nested_value")
        
        assert manager.get("level1.level2.key") == "nested_value"
    
    def test_config_manager_config_property(self):
        """Test ConfigManager.config property returns copy."""
        manager = ConfigManager()
        config1 = manager.config
        config2 = manager.config
        
        # Should be equal but not same object
        assert config1 == config2
        config1["modified"] = True
        assert "modified" not in manager.config
