"""Unit tests for the Plugin CLI commands."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from typing import List
from pathlib import Path

from src.presentation.cli import app
from src.presentation.cli.plugin_cmd import app as plugin_app
from src.orchestration.plugin_manager import PluginManager
from src.core.interfaces import AudioProcessor
from src.core.types import ParameterSpec, ProcessorCategory, ProcessResult


runner = CliRunner()


class MockProcessor(AudioProcessor):
    """Mock processor for CLI testing."""
    
    @property
    def name(self) -> str:
        return "mock-cli-processor"
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    @property
    def description(self) -> str:
        return "A mock processor for CLI testing"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.ANALYSIS
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec(
                name="input_mode",
                type="string",
                description="Input mode selection",
                required=True,
                choices=["fast", "slow", "auto"],
            ),
            ParameterSpec(
                name="threshold",
                type="float",
                description="Processing threshold",
                required=False,
                default=0.5,
                min_value=0.0,
                max_value=1.0,
            ),
        ]
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        **kwargs
    ) -> ProcessResult:
        return ProcessResult(
            success=True,
            input_path=input_path,
            output_paths=[output_dir / input_path.name],
        )


class TestPluginListCommand:
    """Tests for 'plugins list' command."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_list_plugins_shows_builtins(self):
        """Should list built-in processors."""
        result = runner.invoke(app, ["plugins", "list"])
        
        assert result.exit_code == 0
        assert "splitter-fixed" in result.output
        assert "converter" in result.output
    
    def test_list_plugins_shows_table(self):
        """Should display processors in a table format."""
        result = runner.invoke(app, ["plugins", "list"])
        
        assert result.exit_code == 0
        assert "Name" in result.output
        assert "Version" in result.output
        assert "Category" in result.output
        assert "Description" in result.output
    
    def test_list_plugins_verbose(self):
        """Verbose flag should show parameters."""
        result = runner.invoke(app, ["plugins", "list", "--verbose"])
        
        assert result.exit_code == 0
        assert "Parameters" in result.output
    
    def test_list_plugins_filter_by_category(self):
        """Should filter by category."""
        result = runner.invoke(app, ["plugins", "list", "--category", "manipulation"])
        
        assert result.exit_code == 0
        assert "splitter-fixed" in result.output or "converter" in result.output
    
    def test_list_plugins_invalid_category(self):
        """Invalid category should show no results."""
        result = runner.invoke(app, ["plugins", "list", "--category", "nonexistent"])
        
        assert result.exit_code == 1
        assert "No processors found" in result.output
    
    def test_list_plugins_shows_disabled(self):
        """Should show disabled plugins in footer."""
        PluginManager.discover()
        PluginManager.disable("converter")
        
        result = runner.invoke(app, ["plugins", "list"])
        
        assert "Disabled" in result.output
        assert "converter" in result.output


class TestPluginInfoCommand:
    """Tests for 'plugins info' command."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_info_shows_processor_details(self):
        """Should show detailed processor information."""
        result = runner.invoke(app, ["plugins", "info", "splitter-fixed"])
        
        assert result.exit_code == 0
        assert "splitter-fixed" in result.output
        assert "Name:" in result.output
        assert "Version:" in result.output
        assert "Description:" in result.output
    
    def test_info_shows_parameters(self):
        """Should show processor parameters."""
        result = runner.invoke(app, ["plugins", "info", "splitter-fixed"])
        
        assert result.exit_code == 0
        assert "Parameters:" in result.output
        assert "duration_ms" in result.output
    
    def test_info_shows_parameter_constraints(self):
        """Should show parameter constraints."""
        PluginManager.discover()
        PluginManager.register(MockProcessor)
        
        result = runner.invoke(app, ["plugins", "info", "mock-cli-processor"])
        
        assert result.exit_code == 0
        assert "threshold" in result.output
        # Check for constraint info
        assert "min=" in result.output or "max=" in result.output or "choices=" in result.output
    
    def test_info_unknown_processor(self):
        """Unknown processor should show error."""
        result = runner.invoke(app, ["plugins", "info", "nonexistent"])
        
        assert result.exit_code == 1
        assert "Error" in result.output
    
    def test_info_shows_usage_example(self):
        """Should show usage example."""
        result = runner.invoke(app, ["plugins", "info", "splitter-fixed"])
        
        assert result.exit_code == 0
        assert "Usage Example" in result.output


class TestPluginDisableEnableCommands:
    """Tests for 'plugins disable' and 'plugins enable' commands."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_disable_plugin(self):
        """Should disable a plugin."""
        result = runner.invoke(app, ["plugins", "disable", "converter"])
        
        assert result.exit_code == 0
        assert "Disabled" in result.output
        assert "converter" in result.output
        assert PluginManager.is_disabled("converter")
    
    def test_disable_unknown_plugin(self):
        """Disabling unknown plugin should error."""
        result = runner.invoke(app, ["plugins", "disable", "nonexistent"])
        
        assert result.exit_code == 1
        assert "Unknown processor" in result.output
    
    def test_disable_already_disabled(self):
        """Disabling already disabled plugin should not error."""
        PluginManager.discover()
        PluginManager.disable("converter")
        
        result = runner.invoke(app, ["plugins", "disable", "converter"])
        
        # Already disabled is informational, exit code 0
        assert result.exit_code == 0
        assert "already disabled" in result.output
    
    def test_enable_plugin(self):
        """Should enable a disabled plugin."""
        PluginManager.discover()
        PluginManager.disable("converter")
        
        result = runner.invoke(app, ["plugins", "enable", "converter"])
        
        assert result.exit_code == 0
        assert "Enabled" in result.output
        assert not PluginManager.is_disabled("converter")
    
    def test_enable_not_disabled(self):
        """Enabling non-disabled plugin should not error."""
        PluginManager.discover()
        
        result = runner.invoke(app, ["plugins", "enable", "converter"])
        
        assert result.exit_code == 0
        assert "not disabled" in result.output


class TestPluginDiscoverCommand:
    """Tests for 'plugins discover' command."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_discover_plugins(self):
        """Should re-discover plugins."""
        result = runner.invoke(app, ["plugins", "discover"])
        
        assert result.exit_code == 0
        assert "Found" in result.output
        assert "processor" in result.output.lower()
    
    def test_discover_with_include_disabled(self):
        """Should re-enable disabled plugins when flag is set."""
        PluginManager.discover()
        PluginManager.disable("converter")
        
        result = runner.invoke(app, ["plugins", "discover", "--include-disabled"])
        
        assert result.exit_code == 0
        assert not PluginManager.is_disabled("converter")


class TestPluginCommandIntegration:
    """Integration tests for plugin commands."""
    
    def setup_method(self):
        """Reset plugin manager before each test."""
        PluginManager.reset()
    
    def test_help_shows_all_commands(self):
        """Should show all available plugin commands."""
        result = runner.invoke(app, ["plugins", "--help"])
        
        assert result.exit_code == 0
        assert "list" in result.output
        assert "info" in result.output
        assert "disable" in result.output
        assert "enable" in result.output
        assert "discover" in result.output
    
    def test_no_args_shows_help(self):
        """No arguments should show help."""
        result = runner.invoke(app, ["plugins"])
        
        # no_args_is_help=True returns exit code 2 (typer behavior)
        # but still shows usage/help info
        assert "Usage" in result.output or "Commands" in result.output
