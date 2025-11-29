"""Convert command for CLI."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ...processors import get_processor
from ...utils.file_ops import get_audio_files, ensure_directory
from ...utils.progress import create_progress_reporter
from ...utils.logger import setup_logging

app = typer.Typer(help="Convert audio file formats")
console = Console()


@app.command("files")
def convert_files(
    input_path: Path = typer.Argument(
        ...,
        help="Input audio file or directory",
        exists=True,
    ),
    output_format: str = typer.Option(
        "mp3",
        "--format", "-f",
        help="Target audio format",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output directory (default: ./data/output)",
    ),
    bitrate: str = typer.Option(
        "192k",
        "--bitrate", "-b",
        help="Bitrate for lossy formats",
    ),
    normalize: bool = typer.Option(
        False,
        "--normalize", "-n",
        help="Normalize audio levels",
    ),
    remove_silence: bool = typer.Option(
        False,
        "--remove-silence",
        help="Remove leading/trailing silence",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive", "-r",
        help="Process directories recursively",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet", "-q",
        help="Suppress progress output",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose logging",
    ),
):
    """Convert audio files to a different format."""
    import logging
    
    # Setup logging
    level = logging.DEBUG if verbose else logging.INFO
    setup_logging(level=level)
    
    # Default output directory
    if output_dir is None:
        output_dir = Path("data/output")
    ensure_directory(output_dir)
    
    # Get files to process
    if input_path.is_file():
        files = [input_path]
    else:
        files = get_audio_files(input_path, recursive=recursive)
    
    if not files:
        console.print("[yellow]No audio files found[/yellow]")
        raise typer.Exit(1)
    
    console.print(f"[bold]Converting {len(files)} file(s) to {output_format}[/bold]")
    
    # Get processor
    converter = get_processor("converter")
    
    # Progress reporter
    progress = create_progress_reporter(silent=quiet)
    progress.start(len(files), "Converting audio files")
    
    # Process files
    success_count = 0
    fail_count = 0
    
    for i, file_path in enumerate(files, 1):
        result = converter.process(
            input_path=file_path,
            output_dir=output_dir,
            output_format=output_format,
            bitrate=bitrate,
            normalize_audio=normalize,
            remove_silence=remove_silence,
        )
        
        if result.success:
            success_count += 1
        else:
            fail_count += 1
            if not quiet:
                console.print(f"[red]Failed:[/red] {file_path}: {result.error_message}")
        
        progress.update(i)
    
    progress.complete()
    
    # Summary
    console.print()
    console.print(f"[green]✓[/green] Converted: {success_count} files")
    if fail_count > 0:
        console.print(f"[red]✗[/red] Failed: {fail_count} files")
    console.print(f"[blue]Output:[/blue] {output_dir}")


@app.callback()
def callback():
    """Convert audio files between different formats."""
    pass
