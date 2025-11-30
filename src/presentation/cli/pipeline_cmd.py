"""CLI commands for pipeline operations."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...core.exceptions import ConfigError, InvalidYAMLError, ProcessingError
from ...orchestration.pipeline import PipelineEngine
from ...orchestration.pipeline_config import parse_pipeline_config
from ...processors import list_processors
from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer(
    name="pipeline",
    help="Execute multi-step processing pipelines",
    no_args_is_help=True,
)


@app.command("run")
def run_pipeline(
    config: Path = typer.Option(
        ...,
        "--config", "-c",
        help="Path to pipeline YAML config file",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show execution plan without processing",
    ),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume from last checkpoint",
    ),
    resume_from: Optional[int] = typer.Option(
        None,
        "--resume-from",
        help="Resume from specific step number (1-indexed)",
        min=1,
    ),
):
    """
    Execute a processing pipeline from YAML config.
    
    Example:
        audiotoolkit pipeline run --config my_pipeline.yaml
        audiotoolkit pipeline run --config my_pipeline.yaml --dry-run
    """
    try:
        # Parse config
        console.print(f"[blue]Loading config:[/blue] {config}")
        pipeline_config = parse_pipeline_config(config)
        
        # Initialize engine
        engine = PipelineEngine()
        
        if dry_run:
            # Show execution plan
            console.print()
            console.print(Panel(
                "[bold yellow]DRY RUN MODE[/bold yellow]\n"
                "No files will be processed",
                border_style="yellow"
            ))
            console.print()
            
            # Collect output
            lines = []
            engine.dry_run(pipeline_config, output_callback=lines.append)
            
            for line in lines:
                console.print(line)
            
            # Validate and show any issues
            errors = engine.validate(pipeline_config)
            if errors:
                console.print()
                console.print("[bold red]Validation Errors:[/bold red]")
                for error in errors:
                    console.print(f"  [red]✗[/red] {error}")
                raise typer.Exit(code=1)
            else:
                console.print()
                console.print("[bold green]✓ Configuration is valid[/bold green]")
            
        else:
            # Execute pipeline
            console.print(f"[blue]Pipeline:[/blue] {pipeline_config.name}")
            console.print(f"[blue]Steps:[/blue] {len(pipeline_config.steps)}")
            console.print()
            
            session = engine.execute(
                config=pipeline_config,
                resume=resume,
                resume_from_step=resume_from,
            )
            
            # Show results
            console.print()
            console.print(Panel(
                f"[bold green]Pipeline Complete![/bold green]\n\n"
                f"Session ID: {session.session_id}\n"
                f"Total files: {session.total_files}\n"
                f"Processed: {session.processed_count}\n"
                f"Failed: {session.failed_count}",
                border_style="green"
            ))
            
    except InvalidYAMLError as e:
        console.print(f"[red]Invalid YAML:[/red] {e}")
        raise typer.Exit(code=1)
    except ConfigError as e:
        console.print(f"[red]Configuration Error:[/red] {e}")
        raise typer.Exit(code=1)
    except ProcessingError as e:
        console.print(f"[red]Processing Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Unexpected error")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command("validate")
def validate_pipeline(
    config: Path = typer.Option(
        ...,
        "--config", "-c",
        help="Path to pipeline YAML config file",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
):
    """
    Validate pipeline config without executing.
    
    Example:
        audiotoolkit pipeline validate --config my_pipeline.yaml
    """
    try:
        # Parse config
        console.print(f"[blue]Validating:[/blue] {config}")
        pipeline_config = parse_pipeline_config(config)
        
        # Initialize engine and validate
        engine = PipelineEngine()
        errors = engine.validate(pipeline_config)
        
        if errors:
            console.print()
            console.print("[bold red]Validation Failed:[/bold red]")
            for error in errors:
                console.print(f"  [red]✗[/red] {error}")
            raise typer.Exit(code=1)
        else:
            console.print()
            console.print("[bold green]✓ Configuration is valid[/bold green]")
            
            # Show summary
            table = Table(title="Pipeline Summary")
            table.add_column("Property", style="cyan")
            table.add_column("Value")
            
            table.add_row("Name", pipeline_config.name)
            table.add_row("Version", pipeline_config.version)
            table.add_row("Steps", str(len(pipeline_config.steps)))
            table.add_row("Input", pipeline_config.input.path)
            table.add_row("Output", pipeline_config.settings.output_dir)
            
            console.print()
            console.print(table)
            
            # Show steps
            steps_table = Table(title="Steps")
            steps_table.add_column("#", style="dim")
            steps_table.add_column("Name", style="cyan")
            steps_table.add_column("Processor")
            steps_table.add_column("Parameters")
            
            for i, step in enumerate(pipeline_config.steps, start=1):
                params_str = ", ".join(
                    f"{k}={v}" for k, v in step.params.items()
                ) if step.params else "-"
                steps_table.add_row(str(i), step.name, step.processor, params_str)
            
            console.print()
            console.print(steps_table)
            
    except InvalidYAMLError as e:
        console.print(f"[red]Invalid YAML:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Validation error")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command("processors")
def list_available_processors():
    """
    List all available processors for pipelines.
    
    Example:
        audiotoolkit pipeline processors
    """
    from ...processors import get_processor
    
    processors = list_processors()
    
    table = Table(title="Available Processors")
    table.add_column("Name", style="cyan")
    table.add_column("Version")
    table.add_column("Description")
    table.add_column("Category")
    
    for name in processors:
        try:
            proc = get_processor(name)
            table.add_row(
                proc.name,
                proc.version,
                proc.description,
                proc.category.value
            )
        except Exception:
            table.add_row(name, "?", "Error loading processor", "-")
    
    console.print(table)


__all__ = ["app"]
