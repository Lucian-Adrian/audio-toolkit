"""Convert command for CLI."""

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

app = typer.Typer(help="Convert audio file formats")
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
    sample_rate: Optional[int] = typer.Option(
        None,
        "--sample-rate", "-s",
        help="Output sample rate in Hz (default: preserve original)",
    ),
    channels: Optional[int] = typer.Option(
        None,
        "--channels", "-c",
        help="Output channels (1=mono, 2=stereo, default: preserve)",
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
    """Convert audio files to a different format."""
    import logging
    
    # Setup logging
    level = logging.DEBUG if verbose else logging.INFO
    setup_logging(level=level)
    
    # Default output directory
    if output_dir is None:
        output_dir = Path("data/output")
    
    # Get files to process
    if input_path.is_file():
        files = [input_path]
    else:
        files = get_audio_files(input_path, recursive=recursive)
    
    if not files:
        console.print("[yellow]No audio files found[/yellow]")
        raise typer.Exit(1)
    
    # Dry run mode
    if dry_run:
        console.print(Panel.fit(
            f"[bold cyan]Dry Run Mode[/bold cyan]\n"
            f"Would convert {len(files)} file(s) to {output_format}",
            title="🔍 Preview",
        ))
        
        table = Table(title="Files to Convert")
        table.add_column("File", style="cyan")
        table.add_column("Current Format")
        table.add_column("Size", justify="right")
        
        for f in files[:20]:
            size_kb = f.stat().st_size / 1024
            table.add_row(f.name, f.suffix.lstrip("."), f"{size_kb:.1f} KB")
        
        if len(files) > 20:
            table.add_row(f"... and {len(files) - 20} more", "", "")
        
        console.print(table)
        
        options = []
        if normalize:
            options.append("normalize")
        if remove_silence:
            options.append("remove silence")
        if sample_rate:
            options.append(f"resample to {sample_rate}Hz")
        if channels:
            options.append(f"{'mono' if channels == 1 else 'stereo'}")
        
        console.print(f"\n[dim]Output directory: {output_dir}[/dim]")
        console.print(f"[dim]Target format: {output_format} @ {bitrate}[/dim]")
        if options:
            console.print(f"[dim]Processing: {', '.join(options)}[/dim]")
        return
    
    ensure_directory(output_dir)
    
    console.print(f"[bold]Converting {len(files)} file(s) to {output_format}[/bold]")
    
    # Get processor
    converter = get_processor("converter")
    
    # Progress reporter
    progress = create_progress_reporter(silent=quiet)
    progress.start(len(files), "Converting audio files")
    
    # Process files
    success_count = 0
    fail_count = 0
    total_duration_ms = 0
    
    for i, file_path in enumerate(files, 1):
        result = converter.process(
            input_path=file_path,
            output_dir=output_dir,
            output_format=output_format,
            bitrate=bitrate,
            sample_rate=sample_rate,
            channels=channels,
            normalize_audio=normalize,
            remove_silence=remove_silence,
        )
        
        if result.success:
            success_count += 1
            total_duration_ms += result.metadata.get("output_duration_ms", 0)
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
    
    table.add_row("✓ Files converted", f"[green]{success_count}[/green]")
    table.add_row("  Audio processed", _format_duration(total_duration_ms))
    if fail_count > 0:
        table.add_row("✗ Failed", f"[red]{fail_count}[/red]")
    table.add_row("  Output directory", str(output_dir))
    
    console.print(table)


@app.callback()
def callback():
    """Convert audio files between different formats."""
    pass
