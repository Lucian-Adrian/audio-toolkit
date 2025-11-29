"""Split command for CLI."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...processors import get_processor
from ...utils.file_ops import get_audio_files, ensure_directory
from ...utils.progress import create_progress_reporter
from ...utils.logger import setup_logging

app = typer.Typer(help="Split audio files into segments")
console = Console()


def _format_duration(ms: float) -> str:
    """Format milliseconds as human-readable duration."""
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs:.0f}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


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
    min_last_segment: float = typer.Option(
        1.0,
        "--min-last",
        help="Minimum last segment duration (seconds). Shorter segments merge with previous",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive", "-r",
        help="Process directories recursively",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be processed without actually processing",
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
    
    # Convert duration to milliseconds
    duration_ms = duration * 1000
    min_last_segment_ms = min_last_segment * 1000
    
    # Get files to process
    if input_path.is_file():
        files = [input_path]
    else:
        files = get_audio_files(input_path, recursive=recursive)
    
    if not files:
        console.print("[yellow]No audio files found[/yellow]")
        raise typer.Exit(1)
    
    # Dry run mode - show what would be processed
    if dry_run:
        console.print(Panel.fit(
            f"[bold cyan]Dry Run Mode[/bold cyan]\n"
            f"Would process {len(files)} file(s)",
            title="🔍 Preview",
        ))
        
        table = Table(title="Files to Process")
        table.add_column("File", style="cyan")
        table.add_column("Size", justify="right")
        
        for f in files[:20]:  # Show first 20
            size_kb = f.stat().st_size / 1024
            table.add_row(f.name, f"{size_kb:.1f} KB")
        
        if len(files) > 20:
            table.add_row(f"... and {len(files) - 20} more", "")
        
        console.print(table)
        console.print(f"\n[dim]Output directory: {output_dir}[/dim]")
        console.print(f"[dim]Segment duration: {_format_duration(duration_ms)}[/dim]")
        console.print(f"[dim]Output format: {output_format}[/dim]")
        return
    
    ensure_directory(output_dir)
    
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
    total_duration_ms = 0
    
    for i, file_path in enumerate(files, 1):
        result = splitter.process(
            input_path=file_path,
            output_dir=output_dir,
            duration_ms=duration_ms,
            output_format=output_format,
            min_last_segment_ms=min_last_segment_ms,
        )
        
        if result.success:
            success_count += 1
            total_segments += len(result.output_paths)
            total_duration_ms += result.metadata.get("total_duration_ms", 0)
        else:
            fail_count += 1
            if not quiet:
                console.print(f"[red]Failed:[/red] {file_path}: {result.error_message}")
        
        progress.update(i)
    
    progress.complete()
    
    # Summary table
    console.print()
    table = Table(title="Summary", show_header=False, box=None)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    
    table.add_row("✓ Files processed", f"[green]{success_count}[/green]")
    table.add_row("✓ Segments created", f"[green]{total_segments}[/green]")
    table.add_row("  Audio processed", _format_duration(total_duration_ms))
    if fail_count > 0:
        table.add_row("✗ Failed", f"[red]{fail_count}[/red]")
    table.add_row("  Output directory", str(output_dir))
    
    console.print(table)


@app.callback()
def callback():
    """Split audio files into segments using various methods."""
    pass
