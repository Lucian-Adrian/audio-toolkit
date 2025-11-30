"""CLI module using Typer."""

import sys
from typing import Optional

import typer
from rich.console import Console

from .split_cmd import app as split_app
from .convert_cmd import app as convert_app
from .session_cmd import app as session_app
from .pipeline_cmd import app as pipeline_app

console = Console()

# Main CLI app
app = typer.Typer(
    name="audiotoolkit",
    help="Audio Toolkit - Batch audio processing made easy",
    no_args_is_help=False,  # Allow wizard launch with no args
    rich_markup_mode="rich",
)

# Register subcommands
app.add_typer(split_app, name="split", help="Split audio files")
app.add_typer(convert_app, name="convert", help="Convert audio formats")
app.add_typer(session_app, name="sessions", help="Manage processing sessions")
app.add_typer(pipeline_app, name="pipeline", help="Execute processing pipelines")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    wizard: bool = typer.Option(
        False,
        "--wizard", "-w",
        help="Launch interactive wizard mode",
    ),
    preset: Optional[str] = typer.Option(
        None,
        "--preset", "-p",
        help="Execute a saved preset by name",
    ),
    version: bool = typer.Option(
        False,
        "--version", "-V",
        help="Show version information",
    ),
):
    """
    🎵 Audio Toolkit - Batch audio processing made easy.
    
    Run without arguments or with --wizard to launch interactive mode.
    Use --preset NAME to execute a saved configuration.
    """
    # Handle version flag
    if version:
        console.print("[bold]Audio Toolkit[/bold] v0.1.0")
        raise typer.Exit()
    
    # Handle preset execution
    if preset:
        from ..wizard.main_menu import execute_from_preset
        success = execute_from_preset(preset)
        raise typer.Exit(0 if success else 1)
    
    # Launch wizard if no subcommand or --wizard flag
    if ctx.invoked_subcommand is None or wizard:
        from ..wizard import launch, is_interactive_terminal
        
        if not is_interactive_terminal():
            console.print(
                "[yellow]Wizard requires an interactive terminal.[/yellow]\n"
                "Use [cyan]--help[/cyan] for CLI options or "
                "[cyan]--preset NAME[/cyan] to run a saved preset."
            )
            raise typer.Exit(1)
        
        launch()
        raise typer.Exit()


__all__ = ["app"]
