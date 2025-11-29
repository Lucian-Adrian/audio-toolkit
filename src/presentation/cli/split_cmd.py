"""Split command for CLI."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ...processors import get_processor
from ...utils.file_ops import get_audio_files, ensure_directory
from ...utils.progress import create_progress_reporter
from ...utils.logger import setup_logging

app = typer.Typer(help="Split audio files into segments")
console = Console()


@app.command("fixed")
def split_fixed(
    input_path: Path = typer.Argument(
        ...,
        help="Input audio file or directory",
        exists=True,
    ),
    duration: float = typer.Option(
        ...,
        "--duration", "-d",
        help="Segment duration in seconds",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output directory (default: ./data/output)",
    ),
    output_format: str = typer.Option(
        "mp3",
        "--format", "-f",
        help="Output audio format",
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
    """Split audio into fixed-duration segments."""
    import logging
    
    # Setup logging
    level = logging.DEBUG if verbose else logging.INFO
    setup_logging(level=level)
    
    # Default output directory
    if output_dir is None:
        output_dir = Path("data/output")
    ensure_directory(output_dir)
    
    # Convert duration to milliseconds
    duration_ms = duration * 1000
    
    # Get files to process
    if input_path.is_file():
        files = [input_path]
    else:
        files = get_audio_files(input_path, recursive=recursive)
    
    if not files:
        console.print("[yellow]No audio files found[/yellow]")
        raise typer.Exit(1)
    
    console.print(f"[bold]Processing {len(files)} file(s)[/bold]")
    
    # Get processor
    splitter = get_processor("splitter-fixed")
    
    # Progress reporter
    progress = create_progress_reporter(silent=quiet)
    progress.start(len(files), "Splitting audio files")
    
    # Process files
    success_count = 0
    fail_count = 0
    total_segments = 0
    
    for i, file_path in enumerate(files, 1):
        result = splitter.process(
            input_path=file_path,
            output_dir=output_dir,
            duration_ms=duration_ms,
            output_format=output_format,
        )
        
        if result.success:
            success_count += 1
            total_segments += len(result.output_paths)
        else:
            fail_count += 1
            if not quiet:
                console.print(f"[red]Failed:[/red] {file_path}: {result.error_message}")
        
        progress.update(i)
    
    progress.complete()
    
    # Summary
    console.print()
    console.print(f"[green]✓[/green] Processed: {success_count} files")
    console.print(f"[green]✓[/green] Created: {total_segments} segments")
    if fail_count > 0:
        console.print(f"[red]✗[/red] Failed: {fail_count} files")
    console.print(f"[blue]Output:[/blue] {output_dir}")


@app.callback()
def callback():
    """Split audio files into segments using various methods."""
    pass
