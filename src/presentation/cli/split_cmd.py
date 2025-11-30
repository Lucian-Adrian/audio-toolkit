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
from ...orchestration import SQLiteSessionStore, SessionManager
from ...core.types import SessionStatus

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
                splitter = get_processor("splitter-fixed")
                ensure_directory(output_dir)
                
                session = session_manager.run_batch(
                    processor=splitter,
                    input_files=[],  # Not used in resume
                    output_dir=output_dir,
                    config={
                        "duration_ms": duration_ms,
                        "output_format": output_format,
                        "min_last_segment_ms": min_last_segment_ms,
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
        store.close()
        return
    
    ensure_directory(output_dir)
    
    console.print(f"[bold]Processing {len(files)} file(s)[/bold]")
    
    # Get processor
    splitter = get_processor("splitter-fixed")
    
    # Run batch with session tracking
    config = {
        "duration_ms": duration_ms,
        "output_format": output_format,
        "min_last_segment_ms": min_last_segment_ms,
    }
    
    try:
        session = session_manager.run_batch(
            processor=splitter,
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
    
    # Count total segments from completed files
    total_segments = sum(
        len(f.output_paths) for f in session.files 
        if f.status.value == "completed"
    )
    
    table.add_row("✓ Files processed", f"[green]{session.processed_count}[/green]")
    table.add_row("✓ Segments created", f"[green]{total_segments}[/green]")
    if session.failed_count > 0:
        table.add_row("✗ Failed", f"[red]{session.failed_count}[/red]")
    table.add_row("  Session ID", session.session_id[:8] + "...")
    
    console.print(table)


@app.callback()
def callback():
    """Split audio files into segments using various methods."""
    pass
