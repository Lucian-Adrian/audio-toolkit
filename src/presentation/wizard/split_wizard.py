"""Split wizard for interactive audio splitting configuration.

This module provides a guided workflow for configuring and
executing audio split operations.
"""

from pathlib import Path
from typing import Dict, Any, Optional

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .components import (
    prompt_choice,
    prompt_confirm,
    prompt_directory,
    prompt_file_or_directory,
    prompt_number,
    prompt_text,
    show_config_summary,
    show_error,
    show_success,
    show_warning,
)
from .preset_manager import PresetManager

console = Console()


def run_split_wizard() -> None:
    """Run the interactive split wizard flow.
    
    Guides the user through:
    1. Selecting split mode
    2. Configuring mode-specific parameters
    3. Selecting input files/directory
    4. Selecting output directory
    5. Reviewing configuration
    6. Executing the split operation
    7. Optionally saving as preset
    """
    console.print(Panel(
        "[bold]Audio Splitter Wizard[/bold]\n"
        "[dim]Split audio files into segments using various methods[/dim]",
        border_style="cyan",
    ))
    
    # Step 1: Select split mode
    mode = _select_split_mode()
    if mode is None:
        return
    
    # Step 2: Configure mode-specific parameters
    config = _configure_split_params(mode)
    if config is None:
        return
    
    # Step 3: Select input
    input_path = _select_input()
    if input_path is None:
        return
    config["input_path"] = input_path
    
    # Step 4: Check for recursive processing
    if input_path.is_dir():
        config["recursive"] = prompt_confirm(
            "Process subdirectories recursively?",
            default=False,
        )
    
    # Step 5: Select output directory
    output_dir = _select_output()
    if output_dir is None:
        return
    config["output_dir"] = output_dir
    
    # Step 6: Select output format
    config["output_format"] = _select_output_format()
    
    # Step 7: Show summary
    _show_split_summary(mode, config)
    
    # Step 8: Confirm and execute
    if not prompt_confirm("Proceed with this configuration?", default=True):
        console.print("[dim]Operation cancelled.[/dim]")
        return
    
    # Execute
    success = _execute_split(mode, config)
    
    # Step 9: Offer to save preset
    if success and prompt_confirm(
        "Save this configuration as a preset for future use?",
        default=False,
    ):
        _save_split_preset(mode, config)


def _select_split_mode() -> Optional[str]:
    """Select the split mode.
    
    Returns:
        Selected mode string or None if cancelled
    """
    choices = [
        {
            "name": "📏 Fixed duration - Split into equal-length segments",
            "value": "fixed",
        },
        {
            "name": "🔇 Silence detection - Split at pauses/silence",
            "value": "silence",
        },
        {
            "name": "📋 Timestamp file - Split using CSV/JSON timestamps",
            "value": "timestamp",
        },
        {
            "name": "⬅️  Back to main menu",
            "value": "back",
        },
    ]
    
    mode = prompt_choice(
        message="Select split mode",
        choices=choices,
    )
    
    return None if mode == "back" else mode


def _configure_split_params(mode: str) -> Optional[Dict[str, Any]]:
    """Configure mode-specific parameters.
    
    Args:
        mode: Split mode (fixed, silence, timestamp)
        
    Returns:
        Configuration dictionary or None if cancelled
    """
    config: Dict[str, Any] = {"mode": mode}
    
    if mode == "fixed":
        return _configure_fixed_params(config)
    elif mode == "silence":
        return _configure_silence_params(config)
    elif mode == "timestamp":
        return _configure_timestamp_params(config)
    
    return config


def _configure_fixed_params(config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure fixed-duration split parameters."""
    console.print("\n[bold cyan]Fixed Duration Settings[/bold cyan]\n")
    
    # Duration selection
    duration_presets = [
        {"name": "30 seconds", "value": 30},
        {"name": "1 minute", "value": 60},
        {"name": "5 minutes", "value": 300},
        {"name": "10 minutes", "value": 600},
        {"name": "Custom duration", "value": "custom"},
    ]
    
    duration = prompt_choice(
        message="Select segment duration",
        choices=duration_presets,
    )
    
    if duration == "custom":
        duration = prompt_number(
            message="Enter segment duration in seconds",
            min_val=1,
            max_val=3600,
            default=30,
        )
    
    config["duration_ms"] = float(duration) * 1000
    config["duration_seconds"] = float(duration)
    
    # Minimum last segment
    min_last = prompt_number(
        message="Minimum last segment duration (seconds)",
        min_val=0,
        max_val=float(duration),
        default=1.0,
    )
    config["min_last_segment_ms"] = float(min_last) * 1000
    
    return config


def _configure_silence_params(config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure silence-detection split parameters."""
    console.print("\n[bold cyan]Silence Detection Settings[/bold cyan]\n")
    
    show_warning(
        "Silence-based splitting is coming soon!\n"
        "For now, please use fixed-duration splitting.\n"
        "This wizard will be updated when the silence splitter is available."
    )
    
    # Threshold selection
    threshold_presets = [
        {"name": "Quiet (-50 dB) - Detect only deep silence", "value": -50},
        {"name": "Normal (-40 dB) - Standard silence detection", "value": -40},
        {"name": "Sensitive (-30 dB) - Detect softer pauses", "value": -30},
        {"name": "Custom threshold", "value": "custom"},
    ]
    
    threshold = prompt_choice(
        message="Select silence threshold",
        choices=threshold_presets,
    )
    
    if threshold == "custom":
        threshold = prompt_number(
            message="Enter threshold in dB (negative value)",
            min_val=-70,
            max_val=-10,
            default=-40,
        )
    
    config["threshold_db"] = float(threshold)
    
    # Minimum silence duration
    min_silence = prompt_number(
        message="Minimum silence duration (milliseconds)",
        min_val=100,
        max_val=5000,
        default=500,
    )
    config["min_silence_ms"] = float(min_silence)
    
    # Minimum segment length
    min_segment = prompt_number(
        message="Minimum segment length (milliseconds)",
        min_val=1000,
        max_val=60000,
        default=5000,
    )
    config["min_segment_ms"] = float(min_segment)
    
    return config


def _configure_timestamp_params(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Configure timestamp-file split parameters."""
    console.print("\n[bold cyan]Timestamp File Settings[/bold cyan]\n")
    
    show_warning(
        "Timestamp-based splitting is coming soon!\n"
        "For now, please use fixed-duration splitting.\n"
        "This wizard will be updated when the timestamp splitter is available."
    )
    
    # Select timestamp file
    timestamp_file = prompt_file_or_directory(
        message="Select timestamp file (CSV, JSON, or TXT)",
        must_exist=True,
        allow_directory=False,
    )
    config["timestamp_file"] = timestamp_file
    
    # Format detection
    ext = timestamp_file.suffix.lower()
    if ext == ".json":
        config["timestamp_format"] = "json"
    elif ext == ".csv":
        config["timestamp_format"] = "csv"
    else:
        config["timestamp_format"] = "txt"
    
    console.print(f"[dim]Detected format: {config['timestamp_format']}[/dim]")
    
    return config


def _select_input() -> Optional[Path]:
    """Select input file or directory.
    
    Returns:
        Selected path or None if cancelled
    """
    console.print("\n[bold cyan]Input Selection[/bold cyan]\n")
    
    input_type = prompt_choice(
        message="Select input type",
        choices=[
            {"name": "📄 Single file", "value": "file"},
            {"name": "📁 Directory (batch process)", "value": "directory"},
            {"name": "⬅️  Cancel", "value": "cancel"},
        ],
    )
    
    if input_type == "cancel":
        return None
    
    try:
        if input_type == "file":
            return prompt_file_or_directory(
                message="Select input audio file",
                must_exist=True,
                allow_directory=False,
            )
        else:
            return prompt_file_or_directory(
                message="Select input directory",
                must_exist=True,
                allow_directory=True,
            )
    except Exception as e:
        show_error(f"Invalid path: {e}")
        return None


def _select_output() -> Optional[Path]:
    """Select output directory.
    
    Returns:
        Selected path or None if cancelled
    """
    console.print("\n[bold cyan]Output Selection[/bold cyan]\n")
    
    try:
        return prompt_directory(
            message="Select output directory",
            default="./data/output",
            must_exist=False,
        )
    except Exception as e:
        show_error(f"Invalid path: {e}")
        return None


def _select_output_format() -> str:
    """Select output audio format.
    
    Returns:
        Selected format string
    """
    format_choices = [
        {"name": "MP3 - Compressed, widely compatible", "value": "mp3"},
        {"name": "WAV - Uncompressed, lossless", "value": "wav"},
        {"name": "FLAC - Compressed, lossless", "value": "flac"},
        {"name": "OGG - Open source compressed", "value": "ogg"},
        {"name": "Same as input", "value": "same"},
    ]
    
    return prompt_choice(
        message="Select output format",
        choices=format_choices,
        default="mp3",
    )


def _show_split_summary(mode: str, config: Dict[str, Any]) -> None:
    """Display configuration summary.
    
    Args:
        mode: Split mode
        config: Configuration dictionary
    """
    mode_names = {
        "fixed": "Fixed Duration",
        "silence": "Silence Detection",
        "timestamp": "Timestamp File",
    }
    
    summary = {
        "Mode": mode_names.get(mode, mode),
        "Input": config.get("input_path"),
        "Output Directory": config.get("output_dir"),
        "Output Format": config.get("output_format"),
    }
    
    if mode == "fixed":
        summary["Segment Duration"] = f"{config.get('duration_seconds', 30)} seconds"
        summary["Min Last Segment"] = f"{config.get('min_last_segment_ms', 1000) / 1000} seconds"
    elif mode == "silence":
        summary["Threshold"] = f"{config.get('threshold_db', -40)} dB"
        summary["Min Silence"] = f"{config.get('min_silence_ms', 500)} ms"
        summary["Min Segment"] = f"{config.get('min_segment_ms', 5000)} ms"
    elif mode == "timestamp":
        summary["Timestamp File"] = config.get("timestamp_file")
        summary["Format"] = config.get("timestamp_format")
    
    if config.get("recursive"):
        summary["Recursive"] = True
    
    show_config_summary(
        title="Split Configuration",
        config=summary,
        description="Review the settings below before proceeding",
    )


def _execute_split(mode: str, config: Dict[str, Any]) -> bool:
    """Execute the split operation.
    
    Args:
        mode: Split mode
        config: Configuration dictionary
        
    Returns:
        True if successful, False otherwise
    """
    from ...processors import get_processor
    from ...orchestration import SQLiteSessionStore, SessionManager
    from ...utils.file_ops import get_audio_files, ensure_directory
    from ...utils.progress import create_progress_reporter
    
    input_path = config["input_path"]
    output_dir = config["output_dir"]
    
    # Get files to process
    if input_path.is_file():
        files = [input_path]
    else:
        recursive = config.get("recursive", False)
        files = get_audio_files(input_path, recursive=recursive)
    
    if not files:
        show_error("No audio files found to process")
        return False
    
    console.print(f"\n[bold]Found {len(files)} file(s) to process[/bold]\n")
    
    # Ensure output directory exists
    ensure_directory(output_dir)
    
    # Get processor
    processor_name = "splitter-fixed"  # Currently only fixed is implemented
    if mode == "silence":
        processor_name = "splitter-silence"
    elif mode == "timestamp":
        processor_name = "splitter-timestamp"
    
    try:
        processor = get_processor(processor_name)
    except Exception as e:
        show_error(f"Processor not available: {e}")
        return False
    
    # Prepare processor config
    processor_config = {}
    if mode == "fixed":
        processor_config = {
            "duration_ms": config.get("duration_ms", 30000),
            "output_format": config.get("output_format", "mp3"),
            "min_last_segment_ms": config.get("min_last_segment_ms", 1000),
        }
    
    # Handle "same" format option
    if processor_config.get("output_format") == "same":
        processor_config["output_format"] = None  # Preserve original
    
    # Initialize session manager
    store = SQLiteSessionStore()
    progress = create_progress_reporter()
    session_manager = SessionManager(
        store=store,
        checkpoint_interval=100,
        progress=progress,
    )
    
    try:
        with console.status("[bold cyan]Processing...[/bold cyan]"):
            session = session_manager.run_batch(
                processor=processor,
                input_files=files,
                output_dir=output_dir,
                config=processor_config,
            )
        
        # Count total segments
        total_segments = sum(
            len(f.output_paths) for f in session.files
            if f.status.value == "completed"
        )
        
        console.print()
        show_success(
            f"Split complete!\n\n"
            f"Files processed: {session.processed_count}\n"
            f"Segments created: {total_segments}\n"
            f"Failed: {session.failed_count}\n"
            f"Session ID: {session.session_id[:8]}..."
        )
        
        return session.failed_count == 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation interrupted![/yellow]")
        console.print("[dim]Session saved. Use 'audiotoolkit sessions resume' to continue.[/dim]")
        return False
    except Exception as e:
        show_error(f"Processing failed: {e}")
        return False
    finally:
        store.close()


def _save_split_preset(mode: str, config: Dict[str, Any]) -> None:
    """Save current configuration as a preset.
    
    Args:
        mode: Split mode
        config: Configuration dictionary
    """
    name = prompt_text(
        message="Enter preset name",
        required=True,
        validate=lambda x: len(x) >= 2 or "Name must be at least 2 characters",
    )
    
    description = prompt_text(
        message="Enter description (optional)",
        required=False,
    )
    
    # Remove non-serializable items
    preset_config = {
        "mode": mode,
        "input_path": str(config.get("input_path", "")),
        "output_dir": str(config.get("output_dir", "")),
        "output_format": config.get("output_format", "mp3"),
        "recursive": config.get("recursive", False),
    }
    
    if mode == "fixed":
        preset_config["duration_ms"] = config.get("duration_ms", 30000)
        preset_config["min_last_segment_ms"] = config.get("min_last_segment_ms", 1000)
    elif mode == "silence":
        preset_config["threshold_db"] = config.get("threshold_db", -40)
        preset_config["min_silence_ms"] = config.get("min_silence_ms", 500)
        preset_config["min_segment_ms"] = config.get("min_segment_ms", 5000)
    elif mode == "timestamp":
        preset_config["timestamp_file"] = str(config.get("timestamp_file", ""))
    
    preset_manager = PresetManager()
    
    try:
        # Check if exists
        overwrite = False
        if preset_manager.preset_exists(name):
            overwrite = prompt_confirm(
                f"Preset '{name}' already exists. Overwrite?",
                default=False,
            )
            if not overwrite:
                return
        
        preset_manager.save_preset(
            name=name,
            operation="split",
            config=preset_config,
            description=description if description else None,
            overwrite=overwrite,
        )
        
        show_success(f"Saved preset: {name}")
        console.print(f"[dim]Use with: audiotoolkit --preset {name}[/dim]")
        
    except Exception as e:
        show_error(f"Failed to save preset: {e}")
