"""Unit tests for the wizard module."""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch
import tempfile
import shutil

from src.presentation.wizard.preset_manager import PresetManager, PresetConfig
from src.presentation.wizard.components import (
    is_interactive,
    show_config_summary,
)
from src.core.exceptions import ConfigError


class TestPresetManager:
    """Tests for PresetManager class."""
    
    @pytest.fixture
    def temp_preset_dir(self):
        """Create a temporary directory for presets."""
        dir_path = Path(tempfile.mkdtemp())
        yield dir_path
        shutil.rmtree(dir_path, ignore_errors=True)
    
    @pytest.fixture
    def preset_manager(self, temp_preset_dir):
        """Create a preset manager with temporary directory."""
        return PresetManager(preset_dir=temp_preset_dir)
    
    def test_preset_save_load(self, preset_manager):
        """Test preset saving and loading."""
        config = {
            "mode": "fixed",
            "duration_ms": 30000,
            "output_format": "mp3",
        }
        
        # Save preset
        path = preset_manager.save_preset(
            name="test-preset",
            operation="split",
            config=config,
            description="Test description",
        )
        
        assert path.exists()
        assert path.suffix == ".yaml"
        
        # Load preset
        loaded = preset_manager.load_preset("test-preset")
        
        assert loaded["name"] == "test-preset"
        assert loaded["operation"] == "split"
        assert loaded["description"] == "Test description"
        assert loaded["config"]["mode"] == "fixed"
        assert loaded["config"]["duration_ms"] == 30000
    
    def test_preset_list(self, preset_manager):
        """Test listing presets."""
        # Create multiple presets
        preset_manager.save_preset("split-preset", "split", {"mode": "fixed"})
        preset_manager.save_preset("convert-preset", "convert", {"format": "mp3"})
        preset_manager.save_preset("split-preset-2", "split", {"mode": "silence"})
        
        # List all
        all_presets = preset_manager.list_presets()
        assert len(all_presets) == 3
        
        # List by operation
        split_presets = preset_manager.list_presets(operation="split")
        assert len(split_presets) == 2
        
        convert_presets = preset_manager.list_presets(operation="convert")
        assert len(convert_presets) == 1
    
    def test_preset_delete(self, preset_manager):
        """Test preset deletion."""
        preset_manager.save_preset("delete-me", "split", {})
        
        assert preset_manager.preset_exists("delete-me")
        
        result = preset_manager.delete_preset("delete-me")
        assert result is True
        assert not preset_manager.preset_exists("delete-me")
        
        # Delete non-existent
        result = preset_manager.delete_preset("nonexistent")
        assert result is False
    
    def test_preset_exists(self, preset_manager):
        """Test preset existence check."""
        assert not preset_manager.preset_exists("test")
        
        preset_manager.save_preset("test", "split", {})
        
        assert preset_manager.preset_exists("test")
    
    def test_preset_overwrite_protection(self, preset_manager):
        """Test that overwrite protection works."""
        preset_manager.save_preset("protected", "split", {"v": 1})
        
        # Should raise without overwrite flag
        with pytest.raises(ConfigError):
            preset_manager.save_preset("protected", "split", {"v": 2})
        
        # Should work with overwrite flag
        preset_manager.save_preset("protected", "split", {"v": 2}, overwrite=True)
        loaded = preset_manager.load_preset("protected")
        assert loaded["config"]["v"] == 2
    
    def test_preset_load_nonexistent(self, preset_manager):
        """Test loading non-existent preset raises error."""
        with pytest.raises(ConfigError):
            preset_manager.load_preset("nonexistent")
    
    def test_preset_name_sanitization(self, preset_manager):
        """Test that preset names are sanitized for filesystem."""
        # Names with unsafe characters should be sanitized
        preset_manager.save_preset("test/preset:name", "split", {})
        
        # Should still be loadable
        assert preset_manager.preset_exists("test/preset:name")
        loaded = preset_manager.load_preset("test/preset:name")
        assert loaded["name"] == "test_preset_name"
    
    def test_preset_with_path_serialization(self, preset_manager, temp_preset_dir):
        """Test that Path objects are serialized to strings."""
        config = {
            "input_path": temp_preset_dir / "input",
            "output_dir": temp_preset_dir / "output",
        }
        
        preset_manager.save_preset("paths", "split", config)
        loaded = preset_manager.load_preset("paths")
        
        # Paths should be serialized as strings
        assert isinstance(loaded["config"]["input_path"], str)
        assert isinstance(loaded["config"]["output_dir"], str)
    
    def test_preset_info(self, preset_manager):
        """Test getting preset metadata."""
        preset_manager.save_preset(
            "info-test",
            "convert",
            {"format": "wav"},
            description="Info test preset",
        )
        
        info = preset_manager.get_preset_info("info-test")
        
        assert info is not None
        assert info["name"] == "info-test"
        assert info["operation"] == "convert"
        assert info["description"] == "Info test preset"
        assert "format" in info["config_keys"]
    
    def test_preset_export_import(self, preset_manager, temp_preset_dir):
        """Test preset export and import."""
        # Create and export
        preset_manager.save_preset("export-test", "split", {"mode": "fixed"})
        export_path = temp_preset_dir / "exported.yaml"
        preset_manager.export_preset("export-test", export_path)
        
        assert export_path.exists()
        
        # Delete original
        preset_manager.delete_preset("export-test")
        assert not preset_manager.preset_exists("export-test")
        
        # Import back
        imported_name = preset_manager.import_preset(export_path, name="imported")
        assert imported_name == "imported"
        assert preset_manager.preset_exists("imported")


class TestPresetConfig:
    """Tests for PresetConfig model."""
    
    def test_valid_config(self):
        """Test valid configuration creation."""
        config = PresetConfig(
            name="test",
            operation="split",
            config={"mode": "fixed"},
        )
        
        assert config.name == "test"
        assert config.operation == "split"
        assert config.config["mode"] == "fixed"
        assert isinstance(config.created_at, datetime)
    
    def test_name_validation(self):
        """Test name sanitization."""
        config = PresetConfig(
            name="test/name:with<special>chars",
            operation="split",
        )
        
        # Unsafe characters should be replaced
        assert "/" not in config.name or config.name.replace("/", "_") == config.name
    
    def test_empty_name_rejected(self):
        """Test that empty names are rejected."""
        with pytest.raises(Exception):  # Pydantic validation error
            PresetConfig(name="", operation="split")


class TestWizardComponents:
    """Tests for wizard UI components."""
    
    def test_is_interactive_detection(self):
        """Test interactive terminal detection."""
        # In test environment, stdin is typically not a TTY
        # This is more of a smoke test
        result = is_interactive()
        assert isinstance(result, bool)
    
    @patch("src.presentation.wizard.components.console")
    def test_show_config_summary(self, mock_console):
        """Test configuration summary display."""
        config = {
            "mode": "fixed",
            "duration": 30,
            "format": "mp3",
        }
        
        # Should not raise
        show_config_summary("Test Summary", config)
        
        # Console.print should have been called
        assert mock_console.print.called


class TestMainMenu:
    """Tests for main menu functionality."""
    
    @patch("src.presentation.wizard.main_menu.is_interactive")
    def test_is_interactive_terminal(self, mock_is_interactive):
        """Test interactive terminal check."""
        from src.presentation.wizard.main_menu import is_interactive_terminal
        
        mock_is_interactive.return_value = True
        assert is_interactive_terminal() is True
        
        mock_is_interactive.return_value = False
        assert is_interactive_terminal() is False
    
    @patch("src.presentation.wizard.main_menu.console")
    def test_show_welcome_banner(self, mock_console):
        """Test welcome banner display."""
        from src.presentation.wizard.main_menu import show_welcome_banner
        
        show_welcome_banner()
        assert mock_console.print.called
    
    @patch("src.presentation.wizard.main_menu.console")
    def test_show_non_interactive_error(self, mock_console):
        """Test non-interactive error message."""
        from src.presentation.wizard.main_menu import show_non_interactive_error
        
        show_non_interactive_error()
        assert mock_console.print.called


class TestSplitWizard:
    """Tests for split wizard functionality."""
    
    @patch("src.presentation.wizard.split_wizard.prompt_choice")
    def test_select_split_mode_fixed(self, mock_choice):
        """Test split mode selection returns fixed."""
        from src.presentation.wizard.split_wizard import _select_split_mode
        
        mock_choice.return_value = "fixed"
        result = _select_split_mode()
        
        assert result == "fixed"
    
    @patch("src.presentation.wizard.split_wizard.prompt_choice")
    def test_select_split_mode_back(self, mock_choice):
        """Test split mode selection returns None on back."""
        from src.presentation.wizard.split_wizard import _select_split_mode
        
        mock_choice.return_value = "back"
        result = _select_split_mode()
        
        assert result is None


class TestConvertWizard:
    """Tests for convert wizard functionality."""
    
    @patch("src.presentation.wizard.convert_wizard.prompt_choice")
    def test_select_output_format(self, mock_choice):
        """Test output format selection."""
        from src.presentation.wizard.convert_wizard import _select_output_format
        
        mock_choice.return_value = "mp3"
        result = _select_output_format()
        
        assert result == "mp3"


class TestCLIIntegration:
    """Tests for CLI integration with wizard."""
    
    @patch("src.presentation.wizard.main_menu.is_interactive_terminal")
    @patch("src.presentation.wizard.main_menu.launch")
    def test_wizard_launch_on_no_args(self, mock_launch, mock_is_interactive):
        """Test that wizard launches when no args provided."""
        from typer.testing import CliRunner
        from src.presentation.cli import app
        
        mock_is_interactive.return_value = True
        runner = CliRunner()
        
        # The wizard would launch, but we've mocked it
        result = runner.invoke(app, [])
        
        # Should call launch when interactive
        mock_launch.assert_called_once()
    
    @patch("src.presentation.wizard.main_menu.is_interactive_terminal")
    def test_non_interactive_shows_error(self, mock_is_interactive):
        """Test that non-interactive terminal shows error."""
        from typer.testing import CliRunner
        from src.presentation.cli import app
        
        mock_is_interactive.return_value = False
        runner = CliRunner()
        
        result = runner.invoke(app, [])
        
        assert result.exit_code == 1
        assert "interactive terminal" in result.output.lower()
    
    @patch("src.presentation.wizard.main_menu.execute_from_preset")
    def test_preset_execution(self, mock_execute):
        """Test preset execution via --preset flag."""
        from typer.testing import CliRunner
        from src.presentation.cli import app
        
        mock_execute.return_value = True
        runner = CliRunner()
        
        result = runner.invoke(app, ["--preset", "my-preset"])
        
        mock_execute.assert_called_once_with("my-preset")


class TestPresetExecution:
    """Tests for preset execution."""
    
    @pytest.fixture
    def temp_preset_dir(self):
        """Create a temporary directory for presets."""
        dir_path = Path(tempfile.mkdtemp())
        yield dir_path
        shutil.rmtree(dir_path, ignore_errors=True)
    
    @patch("src.presentation.wizard.main_menu.PresetManager")
    @patch("src.presentation.wizard.main_menu.console")
    def test_execute_from_preset_not_found(self, mock_console, mock_pm_class):
        """Test execution with non-existent preset."""
        from src.presentation.wizard.main_menu import execute_from_preset
        
        mock_pm = MagicMock()
        mock_pm.load_preset.side_effect = ConfigError("Not found")
        mock_pm_class.return_value = mock_pm
        
        result = execute_from_preset("nonexistent")
        
        assert result is False
    
    @patch("src.presentation.wizard.main_menu.PresetManager")
    @patch("src.presentation.wizard.main_menu.console")
    def test_execute_from_preset_unknown_operation(self, mock_console, mock_pm_class):
        """Test execution with unknown operation type."""
        from src.presentation.wizard.main_menu import execute_from_preset
        
        mock_pm = MagicMock()
        mock_pm.load_preset.return_value = {
            "operation": "unknown",
            "config": {},
        }
        mock_pm_class.return_value = mock_pm
        
        result = execute_from_preset("test")
        
        assert result is False
