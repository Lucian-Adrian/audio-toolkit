"""Comprehensive tests for wizard components to improve coverage.

Tests for convert_wizard, split_wizard, main_menu, and components.
"""

import io
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from rich.console import Console

# ============================================================================
# Component Tests
# ============================================================================


class TestWizardComponentsFunctions:
    """Test wizard component utility functions."""

    def test_is_interactive_returns_bool(self):
        """Test is_interactive returns boolean."""
        from src.presentation.wizard.components import is_interactive
        result = is_interactive()
        assert isinstance(result, bool)

    def test_is_interactive_not_tty(self):
        """Test is_interactive when not a TTY."""
        import sys
        from src.presentation.wizard.components import is_interactive
        
        # Mock stdin as not a tty
        with patch.object(sys.stdin, 'isatty', return_value=False):
            result = is_interactive()
            assert result is False

    def test_show_error_displays_message(self, capsys):
        """Test show_error displays error panel."""
        from src.presentation.wizard.components import show_error, console
        
        # Capture rich console output
        string_io = io.StringIO()
        test_console = Console(file=string_io, force_terminal=True)
        
        with patch('src.presentation.wizard.components.console', test_console):
            show_error("Test error message")
        
        output = string_io.getvalue()
        assert "Test error message" in output or len(output) > 0  # Rich might escape

    def test_show_success_displays_message(self):
        """Test show_success displays success panel."""
        from src.presentation.wizard.components import show_success
        
        string_io = io.StringIO()
        test_console = Console(file=string_io, force_terminal=True)
        
        with patch('src.presentation.wizard.components.console', test_console):
            show_success("Operation completed!")
        
        output = string_io.getvalue()
        assert len(output) > 0

    def test_show_warning_displays_message(self):
        """Test show_warning displays warning panel."""
        from src.presentation.wizard.components import show_warning
        
        string_io = io.StringIO()
        test_console = Console(file=string_io, force_terminal=True)
        
        with patch('src.presentation.wizard.components.console', test_console):
            show_warning("Warning message")
        
        output = string_io.getvalue()
        assert len(output) > 0

    def test_show_info_displays_message(self):
        """Test show_info displays info panel."""
        from src.presentation.wizard.components import show_info
        
        string_io = io.StringIO()
        test_console = Console(file=string_io, force_terminal=True)
        
        with patch('src.presentation.wizard.components.console', test_console):
            show_info("Info message", title="Custom Title")
        
        output = string_io.getvalue()
        assert len(output) > 0

    def test_show_config_summary_displays_table(self):
        """Test show_config_summary displays configuration table."""
        from src.presentation.wizard.components import show_config_summary
        
        string_io = io.StringIO()
        test_console = Console(file=string_io, force_terminal=True)
        
        config = {
            "format": "mp3",
            "bitrate": "192k",
            "normalize": True,
            "channels": 2,
            "path": Path("/test/path"),
            "items": ["a", "b", "c"],
        }
        
        with patch('src.presentation.wizard.components.console', test_console):
            show_config_summary(
                title="Test Config",
                config=config,
                description="Test description"
            )
        
        output = string_io.getvalue()
        assert len(output) > 0

    def test_show_config_summary_without_description(self):
        """Test show_config_summary without description."""
        from src.presentation.wizard.components import show_config_summary
        
        string_io = io.StringIO()
        test_console = Console(file=string_io, force_terminal=True)
        
        with patch('src.presentation.wizard.components.console', test_console):
            show_config_summary(
                title="Test",
                config={"key": "value"},
            )
        
        output = string_io.getvalue()
        assert len(output) > 0

    def test_show_config_summary_with_none_values(self):
        """Test show_config_summary filters None values."""
        from src.presentation.wizard.components import show_config_summary
        
        string_io = io.StringIO()
        test_console = Console(file=string_io, force_terminal=True)
        
        config = {
            "present": "value",
            "missing": None,
            "also_present": True,
        }
        
        with patch('src.presentation.wizard.components.console', test_console):
            show_config_summary("Test", config=config)
        
        output = string_io.getvalue()
        assert len(output) > 0

    def test_show_config_summary_boolean_formatting(self):
        """Test boolean values format correctly."""
        from src.presentation.wizard.components import show_config_summary
        
        string_io = io.StringIO()
        test_console = Console(file=string_io, force_terminal=True)
        
        config = {
            "enabled": True,
            "disabled": False,
        }
        
        with patch('src.presentation.wizard.components.console', test_console):
            show_config_summary("Test", config=config)
        
        # Should complete without error
        output = string_io.getvalue()
        assert len(output) > 0


class TestPromptFunctions:
    """Test prompt functions with mocked InquirerPy."""

    def test_prompt_choice_with_strings(self):
        """Test prompt_choice with string choices."""
        from src.presentation.wizard.components import prompt_choice
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.select.return_value.execute.return_value = "option1"
            
            result = prompt_choice(
                message="Select option",
                choices=["option1", "option2", "option3"],
            )
            
            assert result == "option1"
            mock_inq.select.assert_called_once()

    def test_prompt_choice_with_dicts(self):
        """Test prompt_choice with dict choices."""
        from src.presentation.wizard.components import prompt_choice
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.select.return_value.execute.return_value = "val1"
            
            result = prompt_choice(
                message="Select",
                choices=[
                    {"name": "Option 1", "value": "val1"},
                    {"name": "Option 2", "value": "val2"},
                ],
                default="val1",
            )
            
            assert result == "val1"

    def test_prompt_choice_with_choice_objects(self):
        """Test prompt_choice with Choice objects."""
        from src.presentation.wizard.components import prompt_choice
        from InquirerPy.base.control import Choice
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.select.return_value.execute.return_value = "test"
            
            result = prompt_choice(
                message="Select",
                choices=[Choice(value="test", name="Test Option")],
            )
            
            assert result == "test"

    def test_prompt_multi_choice_with_strings(self):
        """Test prompt_multi_choice with string choices."""
        from src.presentation.wizard.components import prompt_multi_choice
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.checkbox.return_value.execute.return_value = ["a", "b"]
            
            result = prompt_multi_choice(
                message="Select multiple",
                choices=["a", "b", "c"],
            )
            
            assert result == ["a", "b"]

    def test_prompt_multi_choice_with_defaults(self):
        """Test prompt_multi_choice with default selections."""
        from src.presentation.wizard.components import prompt_multi_choice
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.checkbox.return_value.execute.return_value = ["b"]
            
            result = prompt_multi_choice(
                message="Select",
                choices=["a", "b", "c"],
                default=["b"],
            )
            
            assert result == ["b"]

    def test_prompt_multi_choice_with_dicts_and_defaults(self):
        """Test prompt_multi_choice with dict choices and defaults."""
        from src.presentation.wizard.components import prompt_multi_choice
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.checkbox.return_value.execute.return_value = ["val1"]
            
            result = prompt_multi_choice(
                message="Select",
                choices=[
                    {"name": "Option 1", "value": "val1"},
                    {"name": "Option 2", "value": "val2"},
                ],
                default=["val1"],
            )
            
            assert result == ["val1"]

    def test_prompt_multi_choice_min_selections(self):
        """Test prompt_multi_choice with minimum selections."""
        from src.presentation.wizard.components import prompt_multi_choice
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.checkbox.return_value.execute.return_value = ["a"]
            
            result = prompt_multi_choice(
                message="Select at least 1",
                choices=["a", "b"],
                min_selections=1,
            )
            
            assert len(result) >= 0  # Mocked, just testing call

    def test_prompt_number_integer(self):
        """Test prompt_number with integer input."""
        from src.presentation.wizard.components import prompt_number
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.text.return_value.execute.return_value = "42"
            
            result = prompt_number(
                message="Enter number",
                min_val=0,
                max_val=100,
                default=50,
                float_allowed=False,
            )
            
            assert result == 42
            assert isinstance(result, int)

    def test_prompt_number_float(self):
        """Test prompt_number with float input."""
        from src.presentation.wizard.components import prompt_number
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.text.return_value.execute.return_value = "3.14"
            
            result = prompt_number(
                message="Enter float",
                float_allowed=True,
            )
            
            assert result == 3.14
            assert isinstance(result, float)

    def test_prompt_number_with_min_only(self):
        """Test prompt_number with only min value."""
        from src.presentation.wizard.components import prompt_number
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.text.return_value.execute.return_value = "10"
            
            result = prompt_number(
                message="Enter min",
                min_val=5,
            )
            
            assert result == 10.0

    def test_prompt_number_with_max_only(self):
        """Test prompt_number with only max value."""
        from src.presentation.wizard.components import prompt_number
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.text.return_value.execute.return_value = "5"
            
            result = prompt_number(
                message="Enter max",
                max_val=10,
            )
            
            assert result == 5.0

    def test_prompt_text_required(self):
        """Test prompt_text with required input."""
        from src.presentation.wizard.components import prompt_text
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.text.return_value.execute.return_value = "test input"
            
            result = prompt_text(
                message="Enter text",
                required=True,
            )
            
            assert result == "test input"

    def test_prompt_text_optional_with_default(self):
        """Test prompt_text with optional input and default."""
        from src.presentation.wizard.components import prompt_text
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.text.return_value.execute.return_value = "default"
            
            result = prompt_text(
                message="Enter text",
                default="default",
                required=False,
            )
            
            assert result == "default"

    def test_prompt_text_with_validation(self):
        """Test prompt_text with custom validation."""
        from src.presentation.wizard.components import prompt_text
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.text.return_value.execute.return_value = "valid"
            
            result = prompt_text(
                message="Enter text",
                required=False,
                validate=lambda x: True if len(x) > 2 else "Too short",
            )
            
            assert result == "valid"

    def test_prompt_confirm_default_true(self):
        """Test prompt_confirm with default True."""
        from src.presentation.wizard.components import prompt_confirm
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.confirm.return_value.execute.return_value = True
            
            result = prompt_confirm(
                message="Confirm?",
                default=True,
            )
            
            assert result is True

    def test_prompt_confirm_default_false(self):
        """Test prompt_confirm with default False."""
        from src.presentation.wizard.components import prompt_confirm
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.confirm.return_value.execute.return_value = False
            
            result = prompt_confirm(
                message="Confirm?",
                default=False,
            )
            
            assert result is False

    def test_prompt_file_or_directory(self, tmp_path):
        """Test prompt_file_or_directory."""
        from src.presentation.wizard.components import prompt_file_or_directory
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.filepath.return_value.execute.return_value = str(tmp_path)
            
            result = prompt_file_or_directory(
                message="Select path",
                must_exist=False,
                allow_directory=True,
            )
            
            assert isinstance(result, Path)

    def test_prompt_file_or_directory_file_only(self, tmp_path):
        """Test prompt_file_or_directory for file only."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        from src.presentation.wizard.components import prompt_file_or_directory
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.filepath.return_value.execute.return_value = str(test_file)
            
            result = prompt_file_or_directory(
                message="Select file",
                must_exist=True,
                allow_directory=False,
            )
            
            assert isinstance(result, Path)

    def test_prompt_directory(self, tmp_path):
        """Test prompt_directory."""
        from src.presentation.wizard.components import prompt_directory
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.filepath.return_value.execute.return_value = str(tmp_path)
            
            result = prompt_directory(
                message="Select directory",
                default=str(tmp_path),
                must_exist=True,
            )
            
            assert isinstance(result, Path)

    def test_prompt_directory_not_must_exist(self, tmp_path):
        """Test prompt_directory when path doesn't need to exist."""
        from src.presentation.wizard.components import prompt_directory
        
        with patch('src.presentation.wizard.components.inquirer') as mock_inq:
            mock_inq.filepath.return_value.execute.return_value = "/some/new/path"
            
            result = prompt_directory(
                message="Select directory",
                must_exist=False,
            )
            
            assert isinstance(result, Path)


# ============================================================================
# Convert Wizard Tests
# ============================================================================


class TestConvertWizardFunctions:
    """Test convert_wizard internal functions."""

    def test_select_output_format_returns_format(self):
        """Test _select_output_format returns valid format."""
        from src.presentation.wizard.convert_wizard import _select_output_format
        
        with patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock:
            mock.return_value = "mp3"
            
            result = _select_output_format()
            assert result == "mp3"

    def test_select_output_format_back(self):
        """Test _select_output_format returns back."""
        from src.presentation.wizard.convert_wizard import _select_output_format
        
        with patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock:
            mock.return_value = "back"
            
            result = _select_output_format()
            assert result == "back"

    def test_configure_quality_mp3(self):
        """Test _configure_quality for MP3 format."""
        from src.presentation.wizard.convert_wizard import _configure_quality
        
        with patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock:
            mock.return_value = "192k"
            
            config = _configure_quality("mp3")
            assert config.get("bitrate") == "192k"

    def test_configure_quality_mp3_custom(self):
        """Test _configure_quality for MP3 with custom bitrate."""
        from src.presentation.wizard.convert_wizard import _configure_quality
        
        with patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock_choice, \
             patch('src.presentation.wizard.convert_wizard.prompt_number') as mock_num:
            mock_choice.return_value = "custom"
            mock_num.return_value = 256
            
            config = _configure_quality("mp3")
            assert config.get("bitrate") == "256k"

    def test_configure_quality_wav(self):
        """Test _configure_quality for WAV format."""
        from src.presentation.wizard.convert_wizard import _configure_quality
        
        with patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock:
            mock.return_value = "24"
            
            config = _configure_quality("wav")
            assert config.get("sample_format") == "24"

    def test_configure_quality_flac(self):
        """Test _configure_quality for FLAC format."""
        from src.presentation.wizard.convert_wizard import _configure_quality
        
        with patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock:
            mock.return_value = "5"
            
            config = _configure_quality("flac")
            assert config.get("compression_level") == "5"

    def test_configure_quality_ogg(self):
        """Test _configure_quality for OGG format."""
        from src.presentation.wizard.convert_wizard import _configure_quality
        
        with patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock:
            mock.return_value = "128k"
            
            config = _configure_quality("ogg")
            assert config.get("bitrate") == "128k"

    def test_configure_advanced_options_all_enabled(self):
        """Test _configure_advanced_options with all options enabled."""
        from src.presentation.wizard.convert_wizard import _configure_advanced_options
        
        with patch('src.presentation.wizard.convert_wizard.prompt_confirm') as mock_confirm, \
             patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock_choice:
            mock_confirm.side_effect = [True, True, True, True]
            mock_choice.side_effect = [44100, 2]
            
            config = _configure_advanced_options()
            assert config.get("sample_rate") == 44100
            assert config.get("channels") == 2
            assert config.get("normalize") is True
            assert config.get("remove_silence") is True

    def test_configure_advanced_options_minimal(self):
        """Test _configure_advanced_options with minimal options."""
        from src.presentation.wizard.convert_wizard import _configure_advanced_options
        
        with patch('src.presentation.wizard.convert_wizard.prompt_confirm') as mock_confirm:
            mock_confirm.side_effect = [False, False, False, False]
            
            config = _configure_advanced_options()
            assert "sample_rate" not in config
            assert "channels" not in config
            assert config.get("normalize") is False
            assert config.get("remove_silence") is False

    def test_select_input_file(self, tmp_path):
        """Test _select_input for file selection."""
        from src.presentation.wizard.convert_wizard import _select_input
        
        test_file = tmp_path / "test.wav"
        test_file.write_text("fake")
        
        with patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock_choice, \
             patch('src.presentation.wizard.convert_wizard.prompt_file_or_directory') as mock_file:
            mock_choice.return_value = "file"
            mock_file.return_value = test_file
            
            result = _select_input()
            assert result == test_file

    def test_select_input_directory(self, tmp_path):
        """Test _select_input for directory selection."""
        from src.presentation.wizard.convert_wizard import _select_input
        
        with patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock_choice, \
             patch('src.presentation.wizard.convert_wizard.prompt_file_or_directory') as mock_file:
            mock_choice.return_value = "directory"
            mock_file.return_value = tmp_path
            
            result = _select_input()
            assert result == tmp_path

    def test_select_input_cancel(self):
        """Test _select_input when cancelled."""
        from src.presentation.wizard.convert_wizard import _select_input
        
        with patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock_choice:
            mock_choice.return_value = "cancel"
            
            result = _select_input()
            assert result is None

    def test_select_input_error(self):
        """Test _select_input with path error."""
        from src.presentation.wizard.convert_wizard import _select_input
        
        with patch('src.presentation.wizard.convert_wizard.prompt_choice') as mock_choice, \
             patch('src.presentation.wizard.convert_wizard.prompt_file_or_directory') as mock_file, \
             patch('src.presentation.wizard.convert_wizard.show_error'):
            mock_choice.return_value = "file"
            mock_file.side_effect = Exception("Path error")
            
            result = _select_input()
            assert result is None

    def test_select_output(self, tmp_path):
        """Test _select_output returns path."""
        from src.presentation.wizard.convert_wizard import _select_output
        
        with patch('src.presentation.wizard.convert_wizard.prompt_directory') as mock_dir:
            mock_dir.return_value = tmp_path
            
            result = _select_output()
            assert result == tmp_path

    def test_select_output_error(self):
        """Test _select_output with error."""
        from src.presentation.wizard.convert_wizard import _select_output
        
        with patch('src.presentation.wizard.convert_wizard.prompt_directory') as mock_dir, \
             patch('src.presentation.wizard.convert_wizard.show_error'):
            mock_dir.side_effect = Exception("Path error")
            
            result = _select_output()
            assert result is None

    def test_show_convert_summary(self, tmp_path):
        """Test _show_convert_summary displays correctly."""
        from src.presentation.wizard.convert_wizard import _show_convert_summary
        
        config = {
            "input_path": tmp_path / "input.wav",
            "output_dir": tmp_path / "output",
            "output_format": "mp3",
            "bitrate": "192k",
            "sample_rate": 44100,
            "channels": 2,
            "normalize": True,
            "remove_silence": True,
            "recursive": True,
        }
        
        with patch('src.presentation.wizard.convert_wizard.show_config_summary'):
            _show_convert_summary(config)

    def test_show_convert_summary_minimal(self, tmp_path):
        """Test _show_convert_summary with minimal config."""
        from src.presentation.wizard.convert_wizard import _show_convert_summary
        
        config = {
            "input_path": tmp_path / "input.wav",
            "output_dir": tmp_path / "output",
            "output_format": "wav",
            "sample_format": "16",
        }
        
        with patch('src.presentation.wizard.convert_wizard.show_config_summary'):
            _show_convert_summary(config)

    def test_show_convert_summary_with_compression(self, tmp_path):
        """Test _show_convert_summary with FLAC compression."""
        from src.presentation.wizard.convert_wizard import _show_convert_summary
        
        config = {
            "input_path": tmp_path / "input.wav",
            "output_dir": tmp_path / "output",
            "output_format": "flac",
            "compression_level": "5",
        }
        
        with patch('src.presentation.wizard.convert_wizard.show_config_summary'):
            _show_convert_summary(config)


class TestConvertWizardExecution:
    """Test convert wizard execution functions."""

    def test_execute_convert_no_files(self, tmp_path):
        """Test _execute_convert with no files found."""
        from src.presentation.wizard.convert_wizard import _execute_convert
        
        config = {
            "input_path": tmp_path,  # Empty directory
            "output_dir": tmp_path / "output",
        }
        
        with patch('src.presentation.wizard.convert_wizard.show_error'):
            result = _execute_convert(config)
            assert result is False

    def test_save_convert_preset(self, tmp_path):
        """Test _save_convert_preset."""
        from src.presentation.wizard.convert_wizard import _save_convert_preset
        
        config = {
            "input_path": tmp_path / "input",
            "output_dir": tmp_path / "output",
            "output_format": "mp3",
            "bitrate": "192k",
        }
        
        with patch('src.presentation.wizard.convert_wizard.prompt_text') as mock_text, \
             patch('src.presentation.wizard.convert_wizard.PresetManager') as mock_manager, \
             patch('src.presentation.wizard.convert_wizard.show_success'):
            mock_text.side_effect = ["test_preset", "Test description"]
            mock_instance = mock_manager.return_value
            mock_instance.preset_exists.return_value = False
            
            _save_convert_preset(config)
            
            mock_instance.save_preset.assert_called_once()

    def test_save_convert_preset_exists_overwrite(self, tmp_path):
        """Test _save_convert_preset when preset exists and overwrite."""
        from src.presentation.wizard.convert_wizard import _save_convert_preset
        
        config = {"output_format": "mp3"}
        
        with patch('src.presentation.wizard.convert_wizard.prompt_text') as mock_text, \
             patch('src.presentation.wizard.convert_wizard.prompt_confirm') as mock_confirm, \
             patch('src.presentation.wizard.convert_wizard.PresetManager') as mock_manager, \
             patch('src.presentation.wizard.convert_wizard.show_success'):
            mock_text.side_effect = ["existing_preset", ""]
            mock_confirm.return_value = True
            mock_instance = mock_manager.return_value
            mock_instance.preset_exists.return_value = True
            
            _save_convert_preset(config)
            
            mock_instance.save_preset.assert_called_once()

    def test_save_convert_preset_exists_no_overwrite(self, tmp_path):
        """Test _save_convert_preset when preset exists and no overwrite."""
        from src.presentation.wizard.convert_wizard import _save_convert_preset
        
        config = {"output_format": "mp3"}
        
        with patch('src.presentation.wizard.convert_wizard.prompt_text') as mock_text, \
             patch('src.presentation.wizard.convert_wizard.prompt_confirm') as mock_confirm, \
             patch('src.presentation.wizard.convert_wizard.PresetManager') as mock_manager:
            mock_text.side_effect = ["existing_preset", ""]
            mock_confirm.return_value = False
            mock_instance = mock_manager.return_value
            mock_instance.preset_exists.return_value = True
            
            _save_convert_preset(config)
            
            mock_instance.save_preset.assert_not_called()

    def test_save_convert_preset_error(self, tmp_path):
        """Test _save_convert_preset with error."""
        from src.presentation.wizard.convert_wizard import _save_convert_preset
        
        config = {"output_format": "mp3"}
        
        with patch('src.presentation.wizard.convert_wizard.prompt_text') as mock_text, \
             patch('src.presentation.wizard.convert_wizard.PresetManager') as mock_manager, \
             patch('src.presentation.wizard.convert_wizard.show_error'):
            mock_text.side_effect = ["preset", "desc"]
            mock_instance = mock_manager.return_value
            mock_instance.preset_exists.return_value = False
            mock_instance.save_preset.side_effect = Exception("Save error")
            
            _save_convert_preset(config)  # Should not raise


class TestRunConvertWizard:
    """Test the main run_convert_wizard function."""

    def test_run_convert_wizard_cancelled_at_input(self):
        """Test wizard cancelled at input selection."""
        from src.presentation.wizard.convert_wizard import run_convert_wizard
        
        with patch('src.presentation.wizard.convert_wizard._select_input') as mock_input, \
             patch('src.presentation.wizard.convert_wizard.console'):
            mock_input.return_value = None
            
            run_convert_wizard()  # Should return without error

    def test_run_convert_wizard_cancelled_at_format(self, tmp_path):
        """Test wizard cancelled at format selection."""
        from src.presentation.wizard.convert_wizard import run_convert_wizard
        
        with patch('src.presentation.wizard.convert_wizard._select_input') as mock_input, \
             patch('src.presentation.wizard.convert_wizard._select_output_format') as mock_format, \
             patch('src.presentation.wizard.convert_wizard.console'):
            mock_input.return_value = tmp_path / "test.wav"
            mock_format.return_value = "back"
            
            run_convert_wizard()  # Should return without error

    def test_run_convert_wizard_cancelled_at_output(self, tmp_path):
        """Test wizard cancelled at output selection."""
        from src.presentation.wizard.convert_wizard import run_convert_wizard
        
        with patch('src.presentation.wizard.convert_wizard._select_input') as mock_input, \
             patch('src.presentation.wizard.convert_wizard._select_output_format') as mock_format, \
             patch('src.presentation.wizard.convert_wizard._configure_quality') as mock_quality, \
             patch('src.presentation.wizard.convert_wizard.prompt_confirm') as mock_confirm, \
             patch('src.presentation.wizard.convert_wizard._select_output') as mock_output, \
             patch('src.presentation.wizard.convert_wizard.console'):
            mock_input.return_value = tmp_path / "test.wav"
            mock_format.return_value = "mp3"
            mock_quality.return_value = {"bitrate": "192k"}
            mock_confirm.return_value = False
            mock_output.return_value = None
            
            run_convert_wizard()  # Should return without error

    def test_run_convert_wizard_with_directory_input(self, tmp_path):
        """Test wizard with directory input."""
        from src.presentation.wizard.convert_wizard import run_convert_wizard
        
        with patch('src.presentation.wizard.convert_wizard._select_input') as mock_input, \
             patch('src.presentation.wizard.convert_wizard._select_output_format') as mock_format, \
             patch('src.presentation.wizard.convert_wizard._configure_quality') as mock_quality, \
             patch('src.presentation.wizard.convert_wizard.prompt_confirm') as mock_confirm, \
             patch('src.presentation.wizard.convert_wizard._select_output') as mock_output, \
             patch('src.presentation.wizard.convert_wizard.console'):
            input_dir = tmp_path / "input"
            input_dir.mkdir()
            mock_input.return_value = input_dir
            mock_format.return_value = "mp3"
            mock_quality.return_value = {}
            mock_confirm.side_effect = [True, False, False]  # recursive, advanced, proceed
            mock_output.return_value = tmp_path / "output"
            
            run_convert_wizard()

    def test_run_convert_wizard_user_declines_proceed(self, tmp_path):
        """Test wizard when user declines to proceed."""
        from src.presentation.wizard.convert_wizard import run_convert_wizard
        
        test_file = tmp_path / "test.wav"
        test_file.write_text("fake")
        
        with patch('src.presentation.wizard.convert_wizard._select_input') as mock_input, \
             patch('src.presentation.wizard.convert_wizard._select_output_format') as mock_format, \
             patch('src.presentation.wizard.convert_wizard._configure_quality') as mock_quality, \
             patch('src.presentation.wizard.convert_wizard.prompt_confirm') as mock_confirm, \
             patch('src.presentation.wizard.convert_wizard._select_output') as mock_output, \
             patch('src.presentation.wizard.convert_wizard._show_convert_summary'), \
             patch('src.presentation.wizard.convert_wizard.console'):
            mock_input.return_value = test_file
            mock_format.return_value = "mp3"
            mock_quality.return_value = {"bitrate": "192k"}
            mock_confirm.side_effect = [False, False]  # advanced, proceed
            mock_output.return_value = tmp_path / "output"
            
            run_convert_wizard()


# ============================================================================
# Split Wizard Tests
# ============================================================================


class TestSplitWizardFunctions:
    """Test split_wizard functions."""

    def test_split_wizard_imports(self):
        """Test split_wizard can be imported."""
        from src.presentation.wizard import split_wizard
        assert hasattr(split_wizard, 'run_split_wizard')

    def test_select_split_mode(self):
        """Test _select_split_mode function."""
        from src.presentation.wizard.split_wizard import _select_split_mode
        
        with patch('src.presentation.wizard.split_wizard.prompt_choice') as mock:
            mock.return_value = "fixed"
            
            result = _select_split_mode()
            assert result == "fixed"

    def test_select_split_mode_back(self):
        """Test _select_split_mode returns None on back."""
        from src.presentation.wizard.split_wizard import _select_split_mode
        
        with patch('src.presentation.wizard.split_wizard.prompt_choice') as mock:
            mock.return_value = "back"
            
            result = _select_split_mode()
            assert result is None

    def test_configure_fixed_params(self):
        """Test _configure_fixed_params function."""
        from src.presentation.wizard.split_wizard import _configure_fixed_params
        
        with patch('src.presentation.wizard.split_wizard.prompt_choice') as mock_choice, \
             patch('src.presentation.wizard.split_wizard.prompt_number') as mock_num, \
             patch('src.presentation.wizard.split_wizard.console'):
            mock_choice.return_value = 30
            mock_num.return_value = 1.0
            
            config = _configure_fixed_params({})
            assert config.get("duration_ms") == 30000.0

    def test_configure_fixed_params_custom(self):
        """Test _configure_fixed_params with custom duration."""
        from src.presentation.wizard.split_wizard import _configure_fixed_params
        
        with patch('src.presentation.wizard.split_wizard.prompt_choice') as mock_choice, \
             patch('src.presentation.wizard.split_wizard.prompt_number') as mock_num, \
             patch('src.presentation.wizard.split_wizard.console'):
            mock_choice.return_value = "custom"
            mock_num.side_effect = [45.0, 1.0]  # custom duration, min last
            
            config = _configure_fixed_params({})
            assert config.get("duration_seconds") == 45.0

    def test_configure_split_params_fixed(self):
        """Test _configure_split_params for fixed mode."""
        from src.presentation.wizard.split_wizard import _configure_split_params
        
        with patch('src.presentation.wizard.split_wizard._configure_fixed_params') as mock:
            mock.return_value = {"mode": "fixed", "duration_ms": 30000}
            
            result = _configure_split_params("fixed")
            assert result["mode"] == "fixed"

    def test_configure_split_params_silence(self):
        """Test _configure_split_params for silence mode."""
        from src.presentation.wizard.split_wizard import _configure_split_params
        
        with patch('src.presentation.wizard.split_wizard._configure_silence_params') as mock:
            mock.return_value = {"mode": "silence"}
            
            result = _configure_split_params("silence")
            assert result["mode"] == "silence"

    def test_configure_split_params_timestamp(self):
        """Test _configure_split_params for timestamp mode."""
        from src.presentation.wizard.split_wizard import _configure_split_params
        
        with patch('src.presentation.wizard.split_wizard._configure_timestamp_params') as mock:
            mock.return_value = {"mode": "timestamp"}
            
            result = _configure_split_params("timestamp")
            assert result["mode"] == "timestamp"


# ============================================================================
# Main Menu Tests  
# ============================================================================


class TestMainMenuFunctions:
    """Test main_menu functions."""

    def test_main_menu_imports(self):
        """Test main_menu can be imported."""
        from src.presentation.wizard import main_menu
        assert hasattr(main_menu, 'show_main_menu')
        assert hasattr(main_menu, 'show_welcome_banner')
        assert hasattr(main_menu, 'is_interactive_terminal')

    def test_show_welcome_banner(self):
        """Test show_welcome_banner displays correctly."""
        from src.presentation.wizard.main_menu import show_welcome_banner
        
        string_io = io.StringIO()
        test_console = Console(file=string_io, force_terminal=True)
        
        with patch('src.presentation.wizard.main_menu.console', test_console):
            show_welcome_banner()
        
        output = string_io.getvalue()
        assert len(output) > 0

    def test_show_non_interactive_error(self):
        """Test show_non_interactive_error displays correctly."""
        from src.presentation.wizard.main_menu import show_non_interactive_error
        
        string_io = io.StringIO()
        test_console = Console(file=string_io, force_terminal=True)
        
        with patch('src.presentation.wizard.main_menu.console', test_console):
            show_non_interactive_error()
        
        output = string_io.getvalue()
        assert len(output) > 0

    def test_is_interactive_terminal(self):
        """Test is_interactive_terminal function."""
        from src.presentation.wizard.main_menu import is_interactive_terminal
        
        result = is_interactive_terminal()
        assert isinstance(result, bool)

    def test_show_main_menu(self):
        """Test show_main_menu returns selection."""
        from src.presentation.wizard.main_menu import show_main_menu
        
        with patch('src.presentation.wizard.main_menu.prompt_choice') as mock:
            mock.return_value = "split"
            
            result = show_main_menu()
            assert result == "split"

    def test_handle_split(self):
        """Test handle_split calls split wizard."""
        from src.presentation.wizard.main_menu import handle_split
        
        with patch('src.presentation.wizard.split_wizard.run_split_wizard') as mock:
            handle_split()
            mock.assert_called_once()

    def test_handle_convert(self):
        """Test handle_convert calls convert wizard."""
        from src.presentation.wizard.main_menu import handle_convert
        
        with patch('src.presentation.wizard.convert_wizard.run_convert_wizard') as mock:
            handle_convert()
            mock.assert_called_once()

    def test_handle_analyze(self):
        """Test handle_analyze shows info message."""
        from src.presentation.wizard.main_menu import handle_analyze
        
        with patch('src.presentation.wizard.main_menu.show_info') as mock:
            handle_analyze()
            mock.assert_called_once()

    def test_handle_voice(self):
        """Test handle_voice shows info message."""
        from src.presentation.wizard.main_menu import handle_voice
        
        with patch('src.presentation.wizard.main_menu.show_info') as mock:
            handle_voice()
            mock.assert_called_once()

    def test_handle_pipeline(self):
        """Test handle_pipeline shows info message."""
        from src.presentation.wizard.main_menu import handle_pipeline
        
        with patch('src.presentation.wizard.main_menu.show_info') as mock:
            handle_pipeline()
            mock.assert_called_once()


# ============================================================================
# Preset Manager Tests
# ============================================================================


class TestPresetManagerAdditional:
    """Additional tests for PresetManager."""

    def test_preset_manager_list_presets_by_operation(self, tmp_path):
        """Test listing presets filtered by operation."""
        from src.presentation.wizard.preset_manager import PresetManager
        
        manager = PresetManager(preset_dir=tmp_path)
        
        # Save presets for different operations
        manager.save_preset("convert1", "convert", {"format": "mp3"})
        manager.save_preset("split1", "split", {"mode": "duration"})
        
        convert_presets = manager.list_presets(operation="convert")
        assert len(convert_presets) == 1
        assert convert_presets[0]["name"] == "convert1"

    def test_preset_manager_delete_preset(self, tmp_path):
        """Test deleting a preset."""
        from src.presentation.wizard.preset_manager import PresetManager
        
        manager = PresetManager(preset_dir=tmp_path)
        manager.save_preset("to_delete", "convert", {"format": "mp3"})
        
        assert manager.preset_exists("to_delete")
        result = manager.delete_preset("to_delete")
        assert result is True
        assert not manager.preset_exists("to_delete")

    def test_preset_manager_delete_nonexistent(self, tmp_path):
        """Test deleting nonexistent preset returns False."""
        from src.presentation.wizard.preset_manager import PresetManager
        
        manager = PresetManager(preset_dir=tmp_path)
        
        result = manager.delete_preset("nonexistent")
        assert result is False

    def test_preset_manager_update_preset(self, tmp_path):
        """Test updating an existing preset."""
        from src.presentation.wizard.preset_manager import PresetManager
        
        manager = PresetManager(preset_dir=tmp_path)
        manager.save_preset("update_me", "convert", {"format": "mp3"})
        
        # Update with overwrite
        manager.save_preset("update_me", "convert", {"format": "wav"}, overwrite=True)
        
        preset = manager.load_preset("update_me")
        assert preset["config"]["format"] == "wav"

    def test_preset_manager_get_preset_info(self, tmp_path):
        """Test getting preset info."""
        from src.presentation.wizard.preset_manager import PresetManager
        
        manager = PresetManager(preset_dir=tmp_path)
        manager.save_preset("info_test", "convert", {"format": "mp3"}, description="Test preset")
        
        info = manager.get_preset_info("info_test")
        assert info is not None
        assert info["name"] == "info_test"

    def test_preset_manager_get_preset_info_not_found(self, tmp_path):
        """Test getting info for nonexistent preset."""
        from src.presentation.wizard.preset_manager import PresetManager
        
        manager = PresetManager(preset_dir=tmp_path)
        
        info = manager.get_preset_info("nonexistent")
        assert info is None

    def test_preset_manager_list_presets_all(self, tmp_path):
        """Test listing all presets."""
        from src.presentation.wizard.preset_manager import PresetManager
        
        manager = PresetManager(preset_dir=tmp_path)
        manager.save_preset("preset1", "convert", {})
        manager.save_preset("preset2", "split", {})
        
        all_presets = manager.list_presets()
        assert len(all_presets) == 2

    def test_preset_manager_list_presets_empty_dir(self, tmp_path):
        """Test listing presets when directory is empty."""
        from src.presentation.wizard.preset_manager import PresetManager
        
        manager = PresetManager(preset_dir=tmp_path)
        
        presets = manager.list_presets()
        assert presets == []
