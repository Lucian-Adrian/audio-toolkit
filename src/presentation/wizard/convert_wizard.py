"""Convert wizard for interactive audio format conversion.

This module provides a guided workflow for configuring and
executing audio format conversion operations.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel

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
)
from .preset_manager import PresetManager

console = Console()


def run_convert_wizard() -> None:
    """Run the interactive convert wizard flow.
    
    Guides the user through:
    1. Selecting input files/directory
    2. Selecting output format and quality
    3. Configuring advanced options (normalize, resample, etc.)
    4. Selecting output directory
    5. Reviewing configuration
    6. Executing the conversion
    7. Optionally saving as preset
    """
    console.print(Panel(
        "[bold]Audio Converter Wizard[/bold]\n"
        "[dim]Convert audio files between different formats[/dim]",
        border_style="cyan",
    ))
    
    config: Dict[str, Any] = {}
    
    # Step 1: Select input
    input_path = _select_input()
    if input_path is None:
        return
    config["input_path"] = input_path
    
    # Step 2: Check for recursive processing
    if input_path.is_dir():
        config["recursive"] = prompt_confirm(
            "Process subdirectories recursively?",
            default=False,
        )
    
    # Step 3: Select output format
    output_format = _select_output_format()
    if output_format == "back":
        return
    config["output_format"] = output_format
    
    # Step 4: Configure quality settings
    quality_config = _configure_quality(output_format)
    config.update(quality_config)
    
    # Step 5: Configure advanced options
    if prompt_confirm("Configure advanced options?", default=False):
        advanced_config = _configure_advanced_options()
        config.update(advanced_config)
    
    # Step 6: Select output directory
    output_dir = _select_output()
    if output_dir is None:
        return
    config["output_dir"] = output_dir
    
    # Step 7: Show summary
    _show_convert_summary(config)
    
    # Step 8: Confirm and execute
    if not prompt_confirm("Proceed with this configuration?", default=True):
        console.print("[dim]Operation cancelled.[/dim]")
        return
    
    # Execute
    success = _execute_convert(config)
    
    # Step 9: Offer to save preset
    if success and prompt_confirm(
        "Save this configuration as a preset for future use?",
        default=False,
    ):
        _save_convert_preset(config)


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


def _select_output_format() -> str:
    """Select output audio format.
    
    Returns:
        Selected format string or "back"
    """
    console.print("\n[bold cyan]Output Format[/bold cyan]\n")
    
    format_choices = [
        {"name": "🎵 MP3 - Compressed, widely compatible", "value": "mp3"},
        {"name": "🔊 WAV - Uncompressed, lossless quality", "value": "wav"},
        {"name": "💿 FLAC - Compressed, lossless", "value": "flac"},
        {"name": "🎶 OGG - Open source, good compression", "value": "ogg"},
        {"name": "📱 AAC/M4A - Modern compression", "value": "m4a"},
        {"name": "⬅️  Back", "value": "back"},
    ]
    
    return prompt_choice(
        message="Select output format",
        choices=format_choices,
    )


def _configure_quality(output_format: str) -> Dict[str, Any]:
    """Configure quality settings based on format.
    
    Args:
        output_format: Selected output format
        
    Returns:
        Quality configuration dictionary
    """
    config: Dict[str, Any] = {}
    
    console.print("\n[bold cyan]Quality Settings[/bold cyan]\n")
    
    # Bitrate for lossy formats
    if output_format in ("mp3", "ogg", "m4a"):
        bitrate_choices = [
            {"name": "Low (128 kbps) - Smaller files", "value": "128k"},
            {"name": "Medium (192 kbps) - Good balance", "value": "192k"},
            {"name": "High (256 kbps) - Better quality", "value": "256k"},
            {"name": "Maximum (320 kbps) - Best lossy quality", "value": "320k"},
            {"name": "Custom bitrate", "value": "custom"},
        ]
        
        bitrate = prompt_choice(
            message="Select bitrate",
            choices=bitrate_choices,
            default="192k",
        )
        
        if bitrate == "custom":
            br_value = prompt_number(
                message="Enter bitrate in kbps",
                min_val=64,
                max_val=320,
                default=192,
                float_allowed=False,
            )
            bitrate = f"{int(br_value)}k"
        
        config["bitrate"] = bitrate
    
    elif output_format == "wav":
        # Sample format for WAV
        sample_format = prompt_choice(
            message="Select sample format",
            choices=[
                {"name": "16-bit (CD quality)", "value": "16"},
                {"name": "24-bit (Studio quality)", "value": "24"},
                {"name": "32-bit float (Maximum precision)", "value": "32"},
            ],
            default="16",
        )
        config["sample_format"] = sample_format
    
    elif output_format == "flac":
        # Compression level for FLAC
        compression = prompt_choice(
            message="Select compression level",
            choices=[
                {"name": "Fast (level 0) - Larger files, faster", "value": "0"},
                {"name": "Default (level 5) - Good balance", "value": "5"},
                {"name": "Best (level 8) - Smaller files, slower", "value": "8"},
            ],
            default="5",
        )
        config["compression_level"] = compression
    
    return config


def _configure_advanced_options() -> Dict[str, Any]:
    """Configure advanced conversion options.
    
    Returns:
        Advanced options configuration dictionary
    """
    config: Dict[str, Any] = {}
    
    console.print("\n[bold cyan]Advanced Options[/bold cyan]\n")
    
    # Sample rate conversion
    if prompt_confirm("Change sample rate?", default=False):
        sample_rate = prompt_choice(
            message="Select sample rate",
            choices=[
                {"name": "22050 Hz - Low quality/voice", "value": 22050},
                {"name": "44100 Hz - CD quality", "value": 44100},
                {"name": "48000 Hz - Video/broadcast", "value": 48000},
                {"name": "96000 Hz - High resolution", "value": 96000},
            ],
            default=44100,
        )
        config["sample_rate"] = sample_rate
    
    # Channel conversion
    if prompt_confirm("Change channel configuration?", default=False):
        channels = prompt_choice(
            message="Select channels",
            choices=[
                {"name": "Mono (1 channel)", "value": 1},
                {"name": "Stereo (2 channels)", "value": 2},
            ],
        )
        config["channels"] = channels
    
    # Audio normalization
    config["normalize"] = prompt_confirm(
        "Normalize audio levels?",
        default=False,
    )
    
    # Remove silence
    config["remove_silence"] = prompt_confirm(
        "Remove leading/trailing silence?",
        default=False,
    )
    
    return config


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


def _show_convert_summary(config: Dict[str, Any]) -> None:
    """Display configuration summary.
    
    Args:
        config: Configuration dictionary
    """
    summary = {
        "Input": config.get("input_path"),
        "Output Directory": config.get("output_dir"),
        "Output Format": config.get("output_format", "mp3").upper(),
    }
    
    if config.get("bitrate"):
        summary["Bitrate"] = config["bitrate"]
    if config.get("sample_format"):
        summary["Sample Format"] = f"{config['sample_format']}-bit"
    if config.get("compression_level"):
        summary["Compression"] = f"Level {config['compression_level']}"
    if config.get("sample_rate"):
        summary["Sample Rate"] = f"{config['sample_rate']} Hz"
    if config.get("channels"):
        summary["Channels"] = "Mono" if config["channels"] == 1 else "Stereo"
    if config.get("normalize"):
        summary["Normalize"] = True
    if config.get("remove_silence"):
        summary["Remove Silence"] = True
    if config.get("recursive"):
        summary["Recursive"] = True
    
    show_config_summary(
        title="Conversion Configuration",
        config=summary,
        description="Review the settings below before proceeding",
    )


def _execute_convert(config: Dict[str, Any]) -> bool:
    """Execute the conversion operation.
    
    Args:
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
    
    console.print(f"\n[bold]Found {len(files)} file(s) to convert[/bold]\n")
    
    # Ensure output directory exists
    ensure_directory(output_dir)
    
    # Get processor
    try:
        processor = get_processor("converter")
    except Exception as e:
        show_error(f"Converter not available: {e}")
        return False
    
    # Prepare processor config
    processor_config = {
        "output_format": config.get("output_format", "mp3"),
        "bitrate": config.get("bitrate", "192k"),
        "sample_rate": config.get("sample_rate"),
        "channels": config.get("channels"),
        "normalize_audio": config.get("normalize", False),
        "remove_silence": config.get("remove_silence", False),
    }
    
    # Initialize session manager
    store = SQLiteSessionStore()
    progress = create_progress_reporter()
    session_manager = SessionManager(
        store=store,
        checkpoint_interval=100,
        progress=progress,
    )
    
    try:
        with console.status("[bold cyan]Converting...[/bold cyan]"):
            session = session_manager.run_batch(
                processor=processor,
                input_files=files,
                output_dir=output_dir,
                config=processor_config,
            )
        
        console.print()
        show_success(
            f"Conversion complete!\n\n"
            f"Files converted: {session.processed_count}\n"
            f"Failed: {session.failed_count}\n"
            f"Session ID: {session.session_id[:8]}..."
        )
        
        return session.failed_count == 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation interrupted![/yellow]")
        console.print("[dim]Session saved. Use 'audiotoolkit sessions resume' to continue.[/dim]")
        return False
    except Exception as e:
        show_error(f"Conversion failed: {e}")
        return False
    finally:
        store.close()


def _save_convert_preset(config: Dict[str, Any]) -> None:
    """Save current configuration as a preset.
    
    Args:
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
    
    # Prepare preset config
    preset_config = {
        "input_path": str(config.get("input_path", "")),
        "output_dir": str(config.get("output_dir", "")),
        "output_format": config.get("output_format", "mp3"),
        "bitrate": config.get("bitrate", "192k"),
        "sample_rate": config.get("sample_rate"),
        "channels": config.get("channels"),
        "normalize": config.get("normalize", False),
        "remove_silence": config.get("remove_silence", False),
        "recursive": config.get("recursive", False),
    }
    
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
            operation="convert",
            config=preset_config,
            description=description if description else None,
            overwrite=overwrite,
        )
        
        show_success(f"Saved preset: {name}")
        console.print(f"[dim]Use with: audiotoolkit --preset {name}[/dim]")
        
    except Exception as e:
        show_error(f"Failed to save preset: {e}")
