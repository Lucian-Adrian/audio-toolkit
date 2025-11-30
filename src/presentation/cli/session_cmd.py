"""Session management CLI commands."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...orchestration import SQLiteSessionStore, SessionManager
from ...core.types import SessionStatus, FileStatus
from ...core.exceptions import SessionNotFoundError, SessionError

app = typer.Typer(help="Manage processing sessions")
console = Console()


def _format_duration(start: datetime, end: Optional[datetime] = None) -> str:
    """Format duration between two timestamps."""
    if end is None:
        end = datetime.now()
    delta = end - start
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def _status_style(status: SessionStatus) -> str:
    """Get rich style for session status."""
    styles = {
        SessionStatus.IN_PROGRESS: "[yellow]in_progress[/yellow]",
        SessionStatus.COMPLETED: "[green]completed[/green]",
        SessionStatus.FAILED: "[red]failed[/red]",
        SessionStatus.PAUSED: "[cyan]paused[/cyan]",
    }
    return styles.get(status, str(status.value))


def _file_status_style(status: FileStatus) -> str:
    """Get rich style for file status."""
    styles = {
        FileStatus.PENDING: "[dim]pending[/dim]",
        FileStatus.PROCESSING: "[yellow]processing[/yellow]",
        FileStatus.COMPLETED: "[green]completed[/green]",
        FileStatus.FAILED: "[red]failed[/red]",
        FileStatus.SKIPPED: "[cyan]skipped[/cyan]",
    }
    return styles.get(status, str(status.value))


@app.command("list")
def list_sessions(
    limit: int = typer.Option(
        10,
        "--limit", "-n",
        help="Number of sessions to show",
    ),
    status: Optional[str] = typer.Option(
        None,
        "--status", "-s",
        help="Filter by status (in_progress, completed, failed, paused)",
    ),
    db_path: Optional[Path] = typer.Option(
        None,
        "--db",
        help="Path to session database",
    ),
):
    """List recent processing sessions."""
    store = SQLiteSessionStore(db_path)
    
    try:
        sessions = store.list_sessions(status=status, limit=limit)
        
        if not sessions:
            console.print("[yellow]No sessions found[/yellow]")
            return
        
        table = Table(title=f"Recent Sessions (showing {len(sessions)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Processor")
        table.add_column("Status")
        table.add_column("Progress")
        table.add_column("Created")
        table.add_column("Duration")
        
        for session in sessions:
            progress = f"{session.processed_count}/{session.total_files}"
            if session.failed_count > 0:
                progress += f" ([red]{session.failed_count} failed[/red])"
            
            created = session.created_at.strftime("%Y-%m-%d %H:%M")
            duration = _format_duration(session.created_at, session.updated_at)
            
            table.add_row(
                session.session_id[:8] + "...",
                session.processor_name,
                _status_style(session.status),
                progress,
                created,
                duration,
            )
        
        console.print(table)
        
        # Show hint for resumable sessions
        resumable = [s for s in sessions if s.status in (SessionStatus.IN_PROGRESS, SessionStatus.PAUSED)]
        if resumable:
            console.print(
                f"\n[dim]💡 {len(resumable)} session(s) can be resumed. "
                f"Use 'audiotoolkit sessions resume' to continue.[/dim]"
            )
            
    finally:
        store.close()


@app.command("info")
def session_info(
    session_id: str = typer.Argument(
        ...,
        help="Session ID (can be partial, e.g., first 8 characters)",
    ),
    db_path: Optional[Path] = typer.Option(
        None,
        "--db",
        help="Path to session database",
    ),
    show_files: bool = typer.Option(
        False,
        "--files", "-f",
        help="Show individual file statuses",
    ),
):
    """Show detailed information about a session."""
    store = SQLiteSessionStore(db_path)
    
    try:
        # Try to find session by partial ID
        sessions = store.list_sessions(limit=100)
        matching = [s for s in sessions if s.session_id.startswith(session_id)]
        
        if not matching:
            console.print(f"[red]No session found matching: {session_id}[/red]")
            raise typer.Exit(1)
        
        if len(matching) > 1:
            console.print(f"[yellow]Multiple sessions match '{session_id}':[/yellow]")
            for s in matching:
                console.print(f"  - {s.session_id}")
            console.print("[dim]Please provide more characters to uniquely identify the session.[/dim]")
            raise typer.Exit(1)
        
        session = matching[0]
        
        # Display session info
        panel_content = f"""
[bold]Session ID:[/bold] {session.session_id}
[bold]Processor:[/bold] {session.processor_name}
[bold]Status:[/bold] {_status_style(session.status)}
[bold]Created:[/bold] {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}
[bold]Updated:[/bold] {session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
[bold]Duration:[/bold] {_format_duration(session.created_at, session.updated_at)}

[bold]Progress:[/bold]
  Total files: {session.total_files}
  Completed: [green]{session.processed_count}[/green]
  Failed: [red]{session.failed_count}[/red]
  Remaining: {session.total_files - session.processed_count - session.failed_count}
"""
        
        console.print(Panel(panel_content.strip(), title="Session Details", border_style="blue"))
        
        # Show config
        if session.config:
            console.print("\n[bold]Configuration:[/bold]")
            for key, value in session.config.items():
                console.print(f"  {key}: {value}")
        
        # Show files if requested
        if show_files and session.files:
            console.print()
            table = Table(title=f"Files ({len(session.files)} total)")
            table.add_column("File", style="cyan")
            table.add_column("Status")
            table.add_column("Error")
            
            # Show up to 50 files
            for file_record in session.files[:50]:
                error = file_record.error_message[:40] + "..." if file_record.error_message and len(file_record.error_message) > 40 else file_record.error_message or ""
                table.add_row(
                    file_record.file_path.name,
                    _file_status_style(file_record.status),
                    f"[red]{error}[/red]" if error else "",
                )
            
            if len(session.files) > 50:
                table.add_row(f"... and {len(session.files) - 50} more", "", "")
            
            console.print(table)
            
    finally:
        store.close()


@app.command("resume")
def resume_session(
    session_id: Optional[str] = typer.Argument(
        None,
        help="Session ID to resume (default: latest incomplete)",
    ),
    db_path: Optional[Path] = typer.Option(
        None,
        "--db",
        help="Path to session database",
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Force resume even if session appears active",
    ),
):
    """Resume an incomplete session."""
    store = SQLiteSessionStore(db_path)
    manager = SessionManager(store)
    
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
                    console.print(f"  - {s.session_id[:8]}... ({s.processor_name})")
                raise typer.Exit(1)
            
            session = matching[0]
        else:
            # Get latest incomplete
            session = manager.get_resumable_session()
            
            if session is None:
                console.print("[yellow]No incomplete sessions to resume[/yellow]")
                console.print("[dim]All sessions are either completed or failed.[/dim]")
                raise typer.Exit(0)
        
        # Check if resumable
        if session.status == SessionStatus.COMPLETED:
            console.print(f"[red]Session {session.session_id[:8]}... is already completed[/red]")
            raise typer.Exit(1)
        
        if session.status == SessionStatus.FAILED:
            console.print(f"[red]Session {session.session_id[:8]}... has failed[/red]")
            console.print("[dim]Start a new session instead.[/dim]")
            raise typer.Exit(1)
        
        if session.status == SessionStatus.IN_PROGRESS and not force:
            console.print(f"[yellow]Session {session.session_id[:8]}... appears to be active[/yellow]")
            console.print("[dim]Use --force if you're sure no other process is using it.[/dim]")
            raise typer.Exit(1)
        
        # Show resume info
        pending = session.total_files - session.processed_count
        console.print(Panel(
            f"[bold]Resuming session[/bold] {session.session_id[:8]}...\n"
            f"Processor: {session.processor_name}\n"
            f"Files remaining: {pending} of {session.total_files}",
            title="🔄 Resume",
            border_style="cyan",
        ))
        
        # The actual resume logic requires the processor - this command just shows info
        # The actual resume is done in split_cmd or convert_cmd with --resume flag
        console.print(
            f"\n[dim]To resume this session, run:[/dim]\n"
            f"  audiotoolkit <command> --resume --session {session.session_id[:8]}"
        )
        
    finally:
        store.close()


@app.command("clean")
def clean_sessions(
    older_than: str = typer.Option(
        "7d",
        "--older-than",
        help="Delete sessions older than this (e.g., 7d, 30d)",
    ),
    db_path: Optional[Path] = typer.Option(
        None,
        "--db",
        help="Path to session database",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be deleted without deleting",
    ),
):
    """Delete old sessions to free up space."""
    # Parse duration
    if older_than.endswith("d"):
        days = int(older_than[:-1])
    elif older_than.endswith("w"):
        days = int(older_than[:-1]) * 7
    elif older_than.endswith("m"):
        days = int(older_than[:-1]) * 30
    else:
        console.print("[red]Invalid duration format. Use: 7d, 2w, or 1m[/red]")
        raise typer.Exit(1)
    
    store = SQLiteSessionStore(db_path)
    
    try:
        if dry_run:
            # Count sessions that would be deleted
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=days)
            sessions = store.list_sessions(limit=1000)
            old_sessions = [s for s in sessions if s.created_at < cutoff]
            
            console.print(f"[yellow]Would delete {len(old_sessions)} session(s) older than {days} days[/yellow]")
            
            if old_sessions:
                table = Table(title="Sessions to be deleted")
                table.add_column("ID")
                table.add_column("Processor")
                table.add_column("Status")
                table.add_column("Created")
                
                for session in old_sessions[:10]:
                    table.add_row(
                        session.session_id[:8] + "...",
                        session.processor_name,
                        session.status.value,
                        session.created_at.strftime("%Y-%m-%d"),
                    )
                
                if len(old_sessions) > 10:
                    table.add_row(f"... and {len(old_sessions) - 10} more", "", "", "")
                
                console.print(table)
        else:
            deleted = store.delete_sessions_older_than(days)
            console.print(f"[green]✓ Deleted {deleted} session(s) older than {days} days[/green]")
            
    finally:
        store.close()


@app.command("delete")
def delete_session(
    session_id: str = typer.Argument(
        ...,
        help="Session ID to delete (can be partial)",
    ),
    db_path: Optional[Path] = typer.Option(
        None,
        "--db",
        help="Path to session database",
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Skip confirmation prompt",
    ),
):
    """Delete a specific session."""
    store = SQLiteSessionStore(db_path)
    
    try:
        # Find session
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
        
        session = matching[0]
        
        # Confirm deletion
        if not force:
            console.print(f"About to delete session [cyan]{session.session_id[:8]}...[/cyan]")
            console.print(f"  Processor: {session.processor_name}")
            console.print(f"  Files: {session.total_files}")
            console.print(f"  Status: {session.status.value}")
            
            confirm = typer.confirm("Are you sure?")
            if not confirm:
                console.print("[dim]Cancelled[/dim]")
                raise typer.Exit(0)
        
        # Delete
        if store.delete_session(session.session_id):
            console.print(f"[green]✓ Deleted session {session.session_id[:8]}...[/green]")
        else:
            console.print(f"[red]Failed to delete session[/red]")
            raise typer.Exit(1)
            
    finally:
        store.close()


@app.callback()
def callback():
    """Manage processing sessions for crash recovery and batch tracking."""
    pass
