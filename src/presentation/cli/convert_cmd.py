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
from ...orchestration import SQLiteSessionStore, SessionManager
from ...core.types import SessionStatus

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
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume the most recent incomplete session",
    ),
    session_id: Optional[str] = typer.Option(
        None,
        "--session",
        help="Specific session ID to resume",
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
    
    # Initialize session store and manager
    store = SQLiteSessionStore()
    progress_reporter = create_progress_reporter(silent=quiet)
    session_manager = SessionManager(
        store=store,
        checkpoint_interval=100,
        progress=progress_reporter
    )
    
    # Handle resume mode
    if resume or session_id:
        try:
            if session_id:
                # Find specific session
                sessions = store.list_sessions(limit=100)
                matching = [s for s in sessions if s.session_id.startswith(session_id)]
                
                if not matching:
                    console.print(f"[red]No session found matching: {session_id}[/red]")
                    raise typer.Exit(1)
                
                if len(matching) > 1:
                    console.print(f"[yellow]Multiple sessions match '{session_id}':[/yellow]")
                    for s in matching:
                        console.print(f"  - {s.session_id[:8]}...")
                    raise typer.Exit(1)
                
                resumable_session = matching[0]
            else:
                resumable_session = session_manager.get_resumable_session()
            
            if resumable_session is None:
                console.print("[yellow]No incomplete session found to resume[/yellow]")
                raise typer.Exit(1)
            
            if resumable_session.status == SessionStatus.COMPLETED:
                console.print("[yellow]Session is already completed. Starting new session.[/yellow]")
                resume = False
                session_id = None
            else:
                # Show resume info
                pending = resumable_session.total_files - resumable_session.processed_count
                console.print(Panel(
                    f"[bold]Resuming session[/bold] {resumable_session.session_id[:8]}...\n"
                    f"Files remaining: {pending} of {resumable_session.total_files}",
                    title="🔄 Resume",
                    border_style="cyan",
                ))
                
                # Get processor and run
                converter = get_processor("converter")
                ensure_directory(output_dir)
                
                session = session_manager.run_batch(
                    processor=converter,
                    input_files=[],  # Not used in resume
                    output_dir=output_dir,
                    config={
                        "output_format": output_format,
                        "bitrate": bitrate,
                        "sample_rate": sample_rate,
                        "channels": channels,
                        "normalize_audio": normalize,
                        "remove_silence": remove_silence,
                    },
                    resume_session_id=resumable_session.session_id,
                )
                
                _print_session_summary(session)
                store.close()
                return
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            store.close()
            raise typer.Exit(1)
    
    # Get files to process
    if input_path.is_file():
        files = [input_path]
    else:
        files = get_audio_files(input_path, recursive=recursive)
    
    if not files:
        console.print("[yellow]No audio files found[/yellow]")
        store.close()
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
        store.close()
        return
    
    ensure_directory(output_dir)
    
    console.print(f"[bold]Converting {len(files)} file(s) to {output_format}[/bold]")
    
    # Get processor
    converter = get_processor("converter")
    
    # Run batch with session tracking
    config = {
        "output_format": output_format,
        "bitrate": bitrate,
        "sample_rate": sample_rate,
        "channels": channels,
        "normalize_audio": normalize,
        "remove_silence": remove_silence,
    }
    
    try:
        session = session_manager.run_batch(
            processor=converter,
            input_files=files,
            output_dir=output_dir,
            config=config,
        )
        
        _print_session_summary(session)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted! Session saved. Use 'audiotoolkit sessions resume' to continue.[/yellow]")
        raise typer.Exit(130)
    finally:
        store.close()


def _print_session_summary(session):
    """Print session summary table."""
    # Summary table
    console.print()
    table = Table(title="Summary", show_header=False, box=None)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    
    table.add_row("✓ Files converted", f"[green]{session.processed_count}[/green]")
    if session.failed_count > 0:
        table.add_row("✗ Failed", f"[red]{session.failed_count}[/red]")
    table.add_row("  Session ID", session.session_id[:8] + "...")
    
    console.print(table)


@app.callback()
def callback():
    """Convert audio files between different formats."""
    pass
