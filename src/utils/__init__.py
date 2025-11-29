"""Utility modules for the audio toolkit."""

from .logger import setup_logging, get_logger, logger, console
from .file_ops import (
    ensure_directory,
    scan_audio_files,
    get_audio_files,
    validate_input_path,
    validate_output_directory,
    is_supported_format,
    generate_output_filename,
    SUPPORTED_FORMATS,
)
from .audio import (
    load_audio,
    get_audio_info,
    export_audio,
    get_duration_ms,
    split_audio,
    calculate_segments,
)
from .config import (
    load_json_config,
    save_json_config,
    get_config_value,
    merge_configs,
    ConfigManager,
    DEFAULT_CONFIG,
)
from .progress import (
    RichProgressReporter,
    SilentProgressReporter,
    create_progress_reporter,
)
from .validators import (
    validate_input_file,
    validate_output_directory as validate_output_dir,
    validate_duration,
    validate_positive_number,
    validate_format,
    collect_validation_errors,
)

__all__ = [
    # Logger
    "setup_logging",
    "get_logger",
    "logger",
    "console",
    # File ops
    "ensure_directory",
    "scan_audio_files",
    "get_audio_files",
    "validate_input_path",
    "validate_output_directory",
    "is_supported_format",
    "generate_output_filename",
    "SUPPORTED_FORMATS",
    # Audio
    "load_audio",
    "get_audio_info",
    "export_audio",
    "get_duration_ms",
    "split_audio",
    "calculate_segments",
    # Config
    "load_json_config",
    "save_json_config",
    "get_config_value",
    "merge_configs",
    "ConfigManager",
    "DEFAULT_CONFIG",
    # Progress
    "RichProgressReporter",
    "SilentProgressReporter",
    "create_progress_reporter",
    # Validators
    "validate_input_file",
    "validate_output_dir",
    "validate_duration",
    "validate_positive_number",
    "validate_format",
    "collect_validation_errors",
]
