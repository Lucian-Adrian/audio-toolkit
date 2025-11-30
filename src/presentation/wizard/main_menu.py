"""Main menu for the interactive wizard.

This module provides the entry point for the interactive TUI mode,
displaying the main menu and routing to specific wizard flows.
"""

import sys
from pathlib import Path
from typing import NoReturn, Optional

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .components import (
    is_interactive,
    prompt_choice,
    prompt_confirm,
    show_error,
    show_info,
    show_success,
)
from .preset_manager import PresetManager

console = Console()


def is_interactive_terminal() -> bool:
    """Check if running in an interactive terminal.
    
    Returns:
        True if stdin/stdout are connected to a TTY
    """
    return is_interactive()


def show_welcome_banner() -> None:
    """Display the welcome banner."""
    banner = """
[bold cyan]🎵 Audio Toolkit[/bold cyan]
[dim]Interactive Wizard Mode[/dim]

[italic]Batch audio processing made easy[/italic]
"""
    console.print(Panel(
        banner.strip(),
        border_style="blue",
        padding=(1, 2),
    ))


def show_non_interactive_error() -> None:
    """Show error message when not in interactive mode."""
    console.print(Panel(
        "[yellow]Wizard requires an interactive terminal.[/yellow]\n\n"
        "Use CLI flags instead:\n"
        "  [cyan]audiotoolkit split fixed --help[/cyan]\n"
        "  [cyan]audiotoolkit convert files --help[/cyan]\n\n"
        "Or use a preset:\n"
        "  [cyan]audiotoolkit --preset my-preset[/cyan]",
        title="[bold yellow]Non-Interactive Mode[/bold yellow]",
        border_style="yellow",
    ))


def show_main_menu() -> str:
    """Display the main menu and return selection.
    
    Returns:
        Selected menu option value
    """
    choices = [
        {"name": "🔪 Split audio files", "value": "split"},
        {"name": "🔄 Convert formats", "value": "convert"},
        {"name": "📊 Analyze audio", "value": "analyze"},
        {"name": "🎤 Voice enhancement", "value": "voice"},
        {"name": "⛓️  Run pipeline", "value": "pipeline"},
        {"name": "💾 Manage presets", "value": "presets"},
        {"name": "📋 View sessions", "value": "sessions"},
        {"name": "⚙️  Settings", "value": "settings"},
        {"name": "❌ Exit", "value": "exit"},
    ]
    
    return prompt_choice(
        message="What would you like to do?",
        choices=choices,
    )


def handle_split() -> None:
    """Handle split operation wizard."""
    from .split_wizard import run_split_wizard
    run_split_wizard()


def handle_convert() -> None:
    """Handle convert operation wizard."""
    from .convert_wizard import run_convert_wizard
    run_convert_wizard()


def handle_analyze() -> None:
    """Handle analyze operation wizard."""
    show_info(
        "Audio analysis features are coming soon!\n\n"
        "Planned features:\n"
        "• Mel-spectrogram visualization\n"
        "• Waveform generation\n"
        "• Audio statistics (RMS, peak, silence ratio)\n"
        "• Voice Activity Detection",
        title="🚧 Coming Soon",
    )


def handle_voice() -> None:
    """Handle voice enhancement wizard."""
    show_info(
        "Voice enhancement features are coming soon!\n\n"
        "Planned features:\n"
        "• Noise reduction\n"
        "• Dynamic range compression\n"
        "• Silence trimming\n"
        "• EQ presets",
        title="🚧 Coming Soon",
    )


def handle_pipeline() -> None:
    """Handle pipeline wizard."""
    show_info(
        "Run a predefined processing pipeline from a YAML file.\n\n"
        "Use the CLI command for now:\n"
        "  [cyan]audiotoolkit pipeline run --config pipeline.yaml[/cyan]",
        title="Pipeline Runner",
    )


def handle_presets() -> None:
    """Handle preset management."""
    preset_manager = PresetManager()
    
    while True:
        choices = [
            {"name": "📋 List all presets", "value": "list"},
            {"name": "📥 Import preset", "value": "import"},
            {"name": "🗑️  Delete preset", "value": "delete"},
            {"name": "⬅️  Back to main menu", "value": "back"},
        ]
        
        action = prompt_choice(
            message="Preset Management",
            choices=choices,
        )
        
        if action == "back":
            break
        elif action == "list":
            _list_presets(preset_manager)
        elif action == "import":
            _import_preset(preset_manager)
        elif action == "delete":
            _delete_preset(preset_manager)


def _list_presets(preset_manager: PresetManager) -> None:
    """Display list of saved presets."""
    presets = preset_manager.list_presets()
    
    if not presets:
        show_info("No presets saved yet.\n\nSave a preset after running any wizard flow.")
        return
    
    table = Table(title="Saved Presets", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Operation", style="green")
    table.add_column("Description")
    table.add_column("Updated")
    
    for preset in presets:
        updated = preset.get("updated_at", "")
        if isinstance(updated, str) and updated:
            # Format datetime string
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(updated)
                updated = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
        
        table.add_row(
            preset.get("name", ""),
            preset.get("operation", ""),
            preset.get("description") or "-",
            str(updated) if updated else "-",
        )
    
    console.print(table)
    console.print()


def _import_preset(preset_manager: PresetManager) -> None:
    """Import a preset from file."""
    from .components import prompt_file_or_directory, prompt_text
    
    try:
        source = prompt_file_or_directory(
            message="Select preset file to import",
            must_exist=True,
            allow_directory=False,
        )
        
        name = prompt_text(
            message="Preset name (leave empty to use file name)",
            required=False,
        )
        
        imported_name = preset_manager.import_preset(
            source_path=source,
            name=name if name else None,
            overwrite=prompt_confirm("Overwrite if exists?", default=False),
        )
        
        show_success(f"Imported preset: {imported_name}")
    except Exception as e:
        show_error(f"Failed to import preset: {e}")


def _delete_preset(preset_manager: PresetManager) -> None:
    """Delete a preset."""
    presets = preset_manager.list_presets()
    
    if not presets:
        show_info("No presets to delete.")
        return
    
    choices = [{"name": p["name"], "value": p["name"]} for p in presets]
    choices.append({"name": "⬅️  Cancel", "value": "cancel"})
    
    name = prompt_choice(
        message="Select preset to delete",
        choices=choices,
    )
    
    if name == "cancel":
        return
    
    if prompt_confirm(f"Delete preset '{name}'?", default=False):
        if preset_manager.delete_preset(name):
            show_success(f"Deleted preset: {name}")
        else:
            show_error(f"Failed to delete preset: {name}")


def handle_sessions() -> None:
    """Handle session management."""
    show_info(
        "Manage your processing sessions.\n\n"
        "Use the CLI commands:\n"
        "  [cyan]audiotoolkit sessions list[/cyan]    - List sessions\n"
        "  [cyan]audiotoolkit sessions resume[/cyan]  - Resume incomplete session\n"
        "  [cyan]audiotoolkit sessions clean[/cyan]   - Clean old sessions",
        title="Session Management",
    )


def handle_settings() -> None:
    """Handle settings menu."""
    show_info(
        "Settings configuration coming soon!\n\n"
        "Current default settings:\n"
        "• Output directory: ./data/output\n"
        "• Default format: mp3\n"
        "• Checkpoint interval: 100 files",
        title="Settings",
    )


def execute_from_preset(preset_name: str) -> bool:
    """Execute an operation from a saved preset.
    
    Args:
        preset_name: Name of the preset to execute
        
    Returns:
        True if execution succeeded, False otherwise
    """
    preset_manager = PresetManager()
    
    try:
        preset_data = preset_manager.load_preset(preset_name)
    except Exception as e:
        show_error(f"Failed to load preset: {e}")
        return False
    
    operation = preset_data.get("operation")
    config = preset_data.get("config", {})
    
    console.print(Panel(
        f"[bold]Executing preset:[/bold] {preset_name}\n"
        f"[dim]Operation: {operation}[/dim]",
        title="🚀 Preset Execution",
        border_style="cyan",
    ))
    
    if operation == "split":
        return _execute_split_preset(config)
    elif operation == "convert":
        return _execute_convert_preset(config)
    else:
        show_error(f"Unknown operation type: {operation}")
        return False


def _execute_split_preset(config: dict) -> bool:
    """Execute a split operation from preset config."""
    from ...processors import get_processor
    from ...orchestration import SQLiteSessionStore, SessionManager
    from ...utils.file_ops import get_audio_files, ensure_directory
    from ...utils.progress import create_progress_reporter
    
    input_path = config.get("input_path")
    output_dir = config.get("output_dir", "./data/output")
    mode = config.get("mode", "fixed")
    
    if not input_path:
        show_error("Preset is missing 'input_path' configuration")
        return False
    
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    if not input_path.exists():
        show_error(f"Input path not found: {input_path}")
        return False
    
    # Get files
    if input_path.is_file():
        files = [input_path]
    else:
        files = get_audio_files(input_path, recursive=config.get("recursive", False))
    
    if not files:
        show_error("No audio files found")
        return False
    
    ensure_directory(output_dir)
    
    # Get processor
    processor_name = f"splitter-{mode}" if mode != "fixed" else "splitter-fixed"
    try:
        processor = get_processor(processor_name)
    except Exception as e:
        show_error(f"Processor not found: {e}")
        return False
    
    # Run batch
    store = SQLiteSessionStore()
    progress = create_progress_reporter()
    session_manager = SessionManager(store=store, progress=progress)
    
    processor_config = {
        "duration_ms": config.get("duration_ms", 30000),
        "output_format": config.get("output_format", "mp3"),
        "min_last_segment_ms": config.get("min_last_segment_ms", 1000),
    }
    
    try:
        session = session_manager.run_batch(
            processor=processor,
            input_files=files,
            output_dir=output_dir,
            config=processor_config,
        )
        
        show_success(
            f"Completed!\n"
            f"Files processed: {session.processed_count}\n"
            f"Failed: {session.failed_count}"
        )
        return True
    except Exception as e:
        show_error(f"Processing failed: {e}")
        return False
    finally:
        store.close()


def _execute_convert_preset(config: dict) -> bool:
    """Execute a convert operation from preset config."""
    from ...processors import get_processor
    from ...orchestration import SQLiteSessionStore, SessionManager
    from ...utils.file_ops import get_audio_files, ensure_directory
    from ...utils.progress import create_progress_reporter
    
    input_path = config.get("input_path")
    output_dir = config.get("output_dir", "./data/output")
    
    if not input_path:
        show_error("Preset is missing 'input_path' configuration")
        return False
    
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    if not input_path.exists():
        show_error(f"Input path not found: {input_path}")
        return False
    
    # Get files
    if input_path.is_file():
        files = [input_path]
    else:
        files = get_audio_files(input_path, recursive=config.get("recursive", False))
    
    if not files:
        show_error("No audio files found")
        return False
    
    ensure_directory(output_dir)
    
    # Get processor
    try:
        processor = get_processor("converter")
    except Exception as e:
        show_error(f"Processor not found: {e}")
        return False
    
    # Run batch
    store = SQLiteSessionStore()
    progress = create_progress_reporter()
    session_manager = SessionManager(store=store, progress=progress)
    
    processor_config = {
        "output_format": config.get("output_format", "mp3"),
        "bitrate": config.get("bitrate", "192k"),
        "sample_rate": config.get("sample_rate"),
        "channels": config.get("channels"),
        "normalize_audio": config.get("normalize", False),
    }
    
    try:
        session = session_manager.run_batch(
            processor=processor,
            input_files=files,
            output_dir=output_dir,
            config=processor_config,
        )
        
        show_success(
            f"Completed!\n"
            f"Files converted: {session.processed_count}\n"
            f"Failed: {session.failed_count}"
        )
        return True
    except Exception as e:
        show_error(f"Processing failed: {e}")
        return False
    finally:
        store.close()


def launch() -> None:
    """Launch the interactive wizard.
    
    This is the main entry point for wizard mode.
    Checks for interactive terminal and displays main menu.
    """
    # Check for interactive terminal
    if not is_interactive_terminal():
        show_non_interactive_error()
        sys.exit(1)
    
    show_welcome_banner()
    
    # Main menu loop
    while True:
        try:
            choice = show_main_menu()
            
            if choice == "exit":
                console.print("\n[dim]Goodbye! 👋[/dim]\n")
                break
            elif choice == "split":
                handle_split()
            elif choice == "convert":
                handle_convert()
            elif choice == "analyze":
                handle_analyze()
            elif choice == "voice":
                handle_voice()
            elif choice == "pipeline":
                handle_pipeline()
            elif choice == "presets":
                handle_presets()
            elif choice == "sessions":
                handle_sessions()
            elif choice == "settings":
                handle_settings()
                
        except KeyboardInterrupt:
            console.print("\n\n[dim]Interrupted. Returning to menu...[/dim]\n")
            continue
        except Exception as e:
            show_error(f"An error occurred: {e}")
            if prompt_confirm("Return to main menu?", default=True):
                continue
            break


if __name__ == "__main__":
    launch()
