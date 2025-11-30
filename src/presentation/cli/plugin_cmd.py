"""CLI commands for plugin management."""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ...orchestration.plugin_manager import PluginManager
from ...core.exceptions import PluginNotFoundError

console = Console()

app = typer.Typer(
    name="plugins",
    help="Manage audio processors and plugins",
    no_args_is_help=True,
)


@app.command("list")
def list_plugins(
    category: Optional[str] = typer.Option(
        None,
        "--category", "-c",
        help="Filter by category (manipulation, analysis, voice, automation)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show additional details including parameters",
    ),
) -> None:
    """List all available audio processors."""
    # Ensure plugins are discovered
    if not PluginManager.is_initialized():
        PluginManager.discover()
    
    processors = PluginManager.list_all()
    
    if not processors:
        console.print("[yellow]No processors available.[/yellow]")
        raise typer.Exit(1)
    
    # Filter by category if specified
    if category:
        category_lower = category.lower()
        processors = {
            name: proc for name, proc in processors.items()
            if proc.category.value.lower() == category_lower
        }
        
        if not processors:
            console.print(f"[yellow]No processors found in category: {category}[/yellow]")
            raise typer.Exit(1)
    
    # Build table
    table = Table(
        title="[bold]Available Processors[/bold]",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name", style="green")
    table.add_column("Version")
    table.add_column("Category", style="magenta")
    table.add_column("Description")
    
    if verbose:
        table.add_column("Parameters", style="dim")
    
    for name in sorted(processors.keys()):
        proc = processors[name]
        
        row = [
            name,
            proc.version,
            proc.category.value,
            proc.description,
        ]
        
        if verbose:
            params = proc.parameters
            param_str = ", ".join(p.name for p in params) if params else "(none)"
            row.append(param_str)
        
        table.add_row(*row)
    
    console.print(table)
    
    # Show disabled plugins if any
    disabled = PluginManager.get_disabled()
    if disabled:
        console.print(f"\n[dim]Disabled: {', '.join(sorted(disabled))}[/dim]")


@app.command("info")
def plugin_info(
    name: str = typer.Argument(
        ...,
        help="Name of the processor to show details for",
    ),
) -> None:
    """Show detailed information about a processor."""
    # Ensure plugins are discovered
    if not PluginManager.is_initialized():
        PluginManager.discover()
    
    try:
        processor = PluginManager.get(name)
    except PluginNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    
    # Build info panel
    info_text = Text()
    info_text.append(f"Name: ", style="bold")
    info_text.append(f"{processor.name}\n", style="green")
    info_text.append(f"Version: ", style="bold")
    info_text.append(f"{processor.version}\n")
    info_text.append(f"Category: ", style="bold")
    info_text.append(f"{processor.category.value}\n", style="magenta")
    info_text.append(f"Description: ", style="bold")
    info_text.append(f"{processor.description}\n")
    
    console.print(Panel(info_text, title=f"[bold cyan]Processor: {name}[/bold cyan]"))
    
    # Parameters table
    params = processor.parameters
    if params:
        console.print("\n[bold]Parameters:[/bold]")
        
        param_table = Table(show_header=True, header_style="bold")
        param_table.add_column("Name", style="cyan")
        param_table.add_column("Type")
        param_table.add_column("Required")
        param_table.add_column("Default")
        param_table.add_column("Description")
        
        for param in params:
            required_str = "[red]Yes[/red]" if param.required else "[dim]No[/dim]"
            default_str = str(param.default) if param.default is not None else "[dim]—[/dim]"
            
            # Build type string with constraints
            type_str = param.type
            constraints = []
            if param.min_value is not None:
                constraints.append(f"min={param.min_value}")
            if param.max_value is not None:
                constraints.append(f"max={param.max_value}")
            if param.choices:
                constraints.append(f"choices={param.choices}")
            
            if constraints:
                type_str += f" ({', '.join(constraints)})"
            
            param_table.add_row(
                param.name,
                type_str,
                required_str,
                default_str,
                param.description,
            )
        
        console.print(param_table)
    else:
        console.print("\n[dim]No parameters[/dim]")
    
    # Usage example
    console.print("\n[bold]Usage Example:[/bold]")
    
    if name.startswith("splitter"):
        console.print(f"  [cyan]audiotoolkit split --processor {name} --input ./audio[/cyan]")
    elif name == "converter":
        console.print(f"  [cyan]audiotoolkit convert --format mp3 --input ./audio[/cyan]")
    else:
        console.print(f"  [cyan]audiotoolkit pipeline run --processor {name} ...[/cyan]")


@app.command("disable")
def disable_plugin(
    name: str = typer.Argument(
        ...,
        help="Name of the processor to disable",
    ),
) -> None:
    """Disable a processor (will be skipped on next load)."""
    # Ensure plugins are discovered
    if not PluginManager.is_initialized():
        PluginManager.discover()
    
    # Check if plugin exists
    if name not in PluginManager.list_names():
        console.print(f"[red]Error:[/red] Unknown processor: {name}")
        raise typer.Exit(1)
    
    # Check if already disabled
    if PluginManager.is_disabled(name):
        console.print(f"[yellow]Processor '{name}' is already disabled.[/yellow]")
        raise typer.Exit(0)
    
    PluginManager.disable(name)
    console.print(f"[green]✓[/green] Disabled processor: [bold]{name}[/bold]")


@app.command("enable")
def enable_plugin(
    name: str = typer.Argument(
        ...,
        help="Name of the processor to enable",
    ),
) -> None:
    """Enable a previously disabled processor."""
    if not PluginManager.is_disabled(name):
        console.print(f"[yellow]Processor '{name}' is not disabled.[/yellow]")
        raise typer.Exit(0)
    
    PluginManager.enable(name)
    console.print(f"[green]✓[/green] Enabled processor: [bold]{name}[/bold]")
    console.print("[dim]Note: Run 'audiotoolkit plugins list' to verify it's loaded.[/dim]")


@app.command("discover")
def rediscover_plugins(
    include_disabled: bool = typer.Option(
        False,
        "--include-disabled",
        help="Also re-enable previously disabled plugins",
    ),
) -> None:
    """Re-discover and reload all plugins."""
    console.print("[dim]Discovering plugins...[/dim]")
    
    PluginManager.discover(include_disabled=include_disabled)
    
    processors = PluginManager.list_all()
    disabled = PluginManager.get_disabled()
    
    console.print(f"[green]✓[/green] Found [bold]{len(processors)}[/bold] processor(s)")
    
    if disabled:
        console.print(f"[yellow]Disabled:[/yellow] {', '.join(sorted(disabled))}")


__all__ = ["app"]
