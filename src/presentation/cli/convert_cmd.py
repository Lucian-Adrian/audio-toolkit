"""Convert command for the CLI."""

import click
from pathlib import Path
from ...processors import registry
from ...utils.audio import load_audio_file
from ...utils.validators import AudioFileValidator, validate_output_directory
from ...utils.progress import get_progress_reporter
from ...core.types import ProcessingConfig
from ...utils.logger import logger


@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory')
@click.option('--format', '-f', default='mp3', help='Output format')
@click.option('--quality', '-q', type=int, default=128, help='Quality/bitrate')
@click.option('--normalize', is_flag=True, help='Normalize audio')
@click.option('--remove-silence', is_flag=True, help='Remove silence')
@click.option('--quiet', is_flag=True, help='Quiet mode')
def convert_cmd(input_file, output_dir, format, quality, normalize, remove_silence, quiet):
    """Convert an audio file to a different format."""
    try:
        input_path = Path(input_file)
        output_dir = Path(output_dir) if output_dir else input_path.parent

        # Validate inputs
        audio_file = load_audio_file(input_path)
        validator = AudioFileValidator()
        if not validator.validate(audio_file):
            errors = validator.get_validation_errors(audio_file)
            click.echo(f"Validation errors: {errors}", err=True)
            return

        validate_output_directory(output_dir)

        # Create processing config
        config = ProcessingConfig(
            output_format=format,
            quality=quality,
            normalize=normalize,
            remove_silence=remove_silence
        )

        # Get converter
        converter_class = registry.get_processor('converter')
        converter = converter_class()

        # Get progress reporter
        progress = get_progress_reporter(not quiet)
        progress.start(1, f"Converting {input_path.name}")

        # Convert the file
        result = converter.process(audio_file, config)

        progress.complete()

        if result.success:
            click.echo(f"Successfully converted to {result.output_file.path}")
        else:
            click.echo(f"Failed to convert: {result.error_message}", err=True)

    except Exception as e:
        logger.error(f"Convert command failed: {e}")
        click.echo(f"Error: {e}", err=True)