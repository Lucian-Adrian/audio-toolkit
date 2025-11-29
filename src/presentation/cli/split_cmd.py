"""Split command for the CLI."""

import click
from pathlib import Path
from ...processors import registry
from ...utils.audio import load_audio_file
from ...utils.validators import AudioFileValidator, validate_output_directory
from ...utils.progress import get_progress_reporter
from ...core.types import SplitConfig
from ...utils.logger import logger


@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory')
@click.option('--method', '-m', default='fixed', help='Split method')
@click.option('--duration', '-d', type=float, help='Duration per segment (seconds)')
@click.option('--prefix', '-p', default='segment', help='Output file prefix')
@click.option('--quiet', '-q', is_flag=True, help='Quiet mode')
def split_cmd(input_file, output_dir, method, duration, prefix, quiet):
    """Split an audio file into segments."""
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

        # Create split config
        config = SplitConfig(
            method=method,
            duration=duration,
            output_prefix=prefix
        )

        # Get splitter
        splitter_class = registry.get_splitter(method)
        splitter = splitter_class()

        # Get progress reporter
        progress = get_progress_reporter(not quiet)
        progress.start(1, f"Splitting {input_path.name}")

        # Split the file
        result = splitter.split(audio_file, config)

        progress.complete()

        if result.success:
            click.echo(f"Successfully split into {len(result.output_files)} segments")
            for i, output_file in enumerate(result.output_files):
                click.echo(f"  {i+1}: {output_file.path}")
        else:
            click.echo(f"Failed to split: {result.error_message}", err=True)

    except Exception as e:
        logger.error(f"Split command failed: {e}")
        click.echo(f"Error: {e}", err=True)