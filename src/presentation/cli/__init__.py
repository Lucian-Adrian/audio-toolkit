"""CLI module using Typer."""

import typer

from .split_cmd import app as split_app
from .convert_cmd import app as convert_app
from .session_cmd import app as session_app

# Main CLI app
app = typer.Typer(
    name="audiotoolkit",
    help="Audio Toolkit - Batch audio processing made easy",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register subcommands
app.add_typer(split_app, name="split", help="Split audio files")
app.add_typer(convert_app, name="convert", help="Convert audio formats")
app.add_typer(session_app, name="sessions", help="Manage processing sessions")


@app.command()
def version():
    """Show version information."""
    from rich.console import Console
    console = Console()
    console.print("[bold]Audio Toolkit[/bold] v0.1.0")


__all__ = ["app"]
