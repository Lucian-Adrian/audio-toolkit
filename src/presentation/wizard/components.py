"""Reusable prompt components for the interactive wizard.

This module provides a consistent set of UI components for
user input across all wizard flows.
"""

import sys
from pathlib import Path
from typing import Any, Callable, List, Optional, TypeVar, Union

from InquirerPy import inquirer
from InquirerPy.validator import PathValidator, EmptyInputValidator
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

T = TypeVar("T")


def is_interactive() -> bool:
    """Check if running in an interactive terminal.
    
    Returns:
        True if stdin is connected to a TTY, False otherwise.
    """
    return sys.stdin.isatty() and sys.stdout.isatty()


def prompt_file_or_directory(
    message: str = "Select input file or directory",
    default: Optional[str] = None,
    must_exist: bool = True,
    allow_directory: bool = True,
) -> Path:
    """Prompt for file or directory selection with path completion.
    
    Args:
        message: Prompt message to display
        default: Default path value
        must_exist: Whether the path must exist
        allow_directory: Whether to allow directory selection
        
    Returns:
        Selected Path object
    """
    validator = PathValidator(
        is_file=not allow_directory,
        is_dir=False,  # Allow both files and directories
        message="Please enter a valid path",
    )
    
    # Only validate existence if required
    if not must_exist:
        validator = None
    
    result = inquirer.filepath(
        message=message,
        default=default or ".",
        validate=validator,
        only_directories=False,
        only_files=not allow_directory,
    ).execute()
    
    return Path(result).resolve()


def prompt_directory(
    message: str = "Select directory",
    default: Optional[str] = None,
    must_exist: bool = False,
) -> Path:
    """Prompt for directory selection.
    
    Args:
        message: Prompt message to display
        default: Default directory path
        must_exist: Whether the directory must exist
        
    Returns:
        Selected Path object
    """
    result = inquirer.filepath(
        message=message,
        default=default or "./data/output",
        only_directories=True,
        validate=PathValidator(
            is_dir=must_exist,
            message="Please enter a valid directory path",
        ) if must_exist else None,
    ).execute()
    
    return Path(result).resolve()


def prompt_choice(
    message: str,
    choices: List[Union[str, dict, Choice]],
    default: Optional[str] = None,
) -> str:
    """Prompt for single choice selection.
    
    Args:
        message: Prompt message to display
        choices: List of choices (strings or dicts with name/value)
        default: Default selection
        
    Returns:
        Selected value (string)
    """
    # Normalize choices
    normalized = []
    for choice in choices:
        if isinstance(choice, str):
            normalized.append(Choice(value=choice, name=choice))
        elif isinstance(choice, dict):
            normalized.append(Choice(
                value=choice.get("value", choice.get("name")),
                name=choice.get("name", choice.get("value")),
            ))
        else:
            normalized.append(choice)
    
    return inquirer.select(
        message=message,
        choices=normalized,
        default=default,
        pointer="❯",
        qmark="?",
    ).execute()


def prompt_multi_choice(
    message: str,
    choices: List[Union[str, dict, Choice]],
    default: Optional[List[str]] = None,
    min_selections: int = 0,
) -> List[str]:
    """Prompt for multiple choice selection.
    
    Args:
        message: Prompt message to display
        choices: List of choices
        default: Default selections
        min_selections: Minimum required selections
        
    Returns:
        List of selected values
    """
    # Normalize choices
    normalized = []
    for choice in choices:
        if isinstance(choice, str):
            enabled = default and choice in default
            normalized.append(Choice(value=choice, name=choice, enabled=enabled))
        elif isinstance(choice, dict):
            value = choice.get("value", choice.get("name"))
            enabled = default and value in default
            normalized.append(Choice(
                value=value,
                name=choice.get("name", value),
                enabled=enabled,
            ))
        else:
            normalized.append(choice)
    
    def validate_min(selections):
        if len(selections) < min_selections:
            return f"Please select at least {min_selections} option(s)"
        return True
    
    return inquirer.checkbox(
        message=message,
        choices=normalized,
        validate=validate_min if min_selections > 0 else None,
        pointer="❯",
        qmark="?",
    ).execute()


def prompt_number(
    message: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    default: Optional[float] = None,
    float_allowed: bool = True,
) -> float:
    """Prompt for numeric input with validation.
    
    Args:
        message: Prompt message to display
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        default: Default value
        float_allowed: Whether to allow floating point numbers
        
    Returns:
        Numeric value (float or int based on float_allowed)
    """
    def validate_number(value: str) -> Union[bool, str]:
        if not value:
            return "Please enter a number"
        try:
            num = float(value) if float_allowed else int(value)
            if min_val is not None and num < min_val:
                return f"Value must be at least {min_val}"
            if max_val is not None and num > max_val:
                return f"Value must be at most {max_val}"
            return True
        except ValueError:
            return "Please enter a valid number"
    
    # Format range hint
    range_hint = ""
    if min_val is not None and max_val is not None:
        range_hint = f" ({min_val}-{max_val})"
    elif min_val is not None:
        range_hint = f" (min: {min_val})"
    elif max_val is not None:
        range_hint = f" (max: {max_val})"
    
    result = inquirer.text(
        message=f"{message}{range_hint}",
        default=str(default) if default is not None else "",
        validate=validate_number,
    ).execute()
    
    return float(result) if float_allowed else int(result)


def prompt_text(
    message: str,
    default: Optional[str] = None,
    required: bool = True,
    validate: Optional[Callable[[str], Union[bool, str]]] = None,
) -> str:
    """Prompt for text input.
    
    Args:
        message: Prompt message to display
        default: Default value
        required: Whether input is required
        validate: Custom validation function
        
    Returns:
        Input text
    """
    validators = []
    if required:
        validators.append(EmptyInputValidator(message="This field is required"))
    
    def combined_validator(value: str) -> Union[bool, str]:
        for v in validators:
            result = v.validate(value)
            if result is not True:
                return result
        if validate:
            return validate(value)
        return True
    
    return inquirer.text(
        message=message,
        default=default or "",
        validate=combined_validator if validators or validate else None,
    ).execute()


def prompt_confirm(
    message: str,
    default: bool = True,
) -> bool:
    """Prompt for yes/no confirmation.
    
    Args:
        message: Confirmation message
        default: Default value (True=yes, False=no)
        
    Returns:
        Boolean confirmation result
    """
    return inquirer.confirm(
        message=message,
        default=default,
    ).execute()


def show_config_summary(
    title: str,
    config: dict,
    description: Optional[str] = None,
) -> None:
    """Display a configuration summary panel.
    
    Args:
        title: Summary title
        config: Configuration dictionary to display
        description: Optional description text
    """
    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=None,
        pad_edge=False,
    )
    table.add_column("Setting", style="bold")
    table.add_column("Value", style="green")
    
    for key, value in config.items():
        if value is not None:
            # Format the value nicely
            if isinstance(value, Path):
                display_value = str(value)
            elif isinstance(value, bool):
                display_value = "✓ Yes" if value else "✗ No"
            elif isinstance(value, (list, tuple)):
                display_value = ", ".join(str(v) for v in value)
            else:
                display_value = str(value)
            
            # Format the key (convert snake_case to Title Case)
            display_key = key.replace("_", " ").title()
            table.add_row(display_key, display_value)
    
    content = table
    if description:
        content = f"[dim]{description}[/dim]\n\n{table}"
    
    console.print(Panel(
        content,
        title=f"[bold]{title}[/bold]",
        border_style="blue",
    ))


def show_error(message: str) -> None:
    """Display an error message.
    
    Args:
        message: Error message to display
    """
    console.print(Panel(
        f"[red]{message}[/red]",
        title="[bold red]Error[/bold red]",
        border_style="red",
    ))


def show_success(message: str) -> None:
    """Display a success message.
    
    Args:
        message: Success message to display
    """
    console.print(Panel(
        f"[green]{message}[/green]",
        title="[bold green]Success[/bold green]",
        border_style="green",
    ))


def show_warning(message: str) -> None:
    """Display a warning message.
    
    Args:
        message: Warning message to display
    """
    console.print(Panel(
        f"[yellow]{message}[/yellow]",
        title="[bold yellow]Warning[/bold yellow]",
        border_style="yellow",
    ))


def show_info(message: str, title: str = "Info") -> None:
    """Display an info message.
    
    Args:
        message: Info message to display
        title: Panel title
    """
    console.print(Panel(
        message,
        title=f"[bold blue]{title}[/bold blue]",
        border_style="blue",
    ))
