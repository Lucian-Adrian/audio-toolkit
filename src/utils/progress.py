"""Progress reporting utilities using Rich."""

from typing import Optional

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from ..core.interfaces import ProgressReporter
from .logger import console


class RichProgressReporter(ProgressReporter):
    """Rich-based progress reporter with beautiful console output."""
    
    def __init__(self):
        self._progress: Optional[Progress] = None
        self._task_id: Optional[int] = None
        self._total: int = 0
    
    def start(self, total: int, description: str = "") -> None:
        """Start progress tracking."""
        self._total = total
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(
            description or "Processing",
            total=total,
        )
    
    def update(self, current: int, message: str = "") -> None:
        """Update progress."""
        if self._progress and self._task_id is not None:
            self._progress.update(
                self._task_id,
                completed=current,
                description=message if message else None,
            )
    
    def advance(self, amount: int = 1) -> None:
        """Advance progress by amount."""
        if self._progress and self._task_id is not None:
            self._progress.advance(self._task_id, amount)
    
    def complete(self, message: str = "") -> None:
        """Mark as complete."""
        if self._progress:
            if self._task_id is not None:
                self._progress.update(self._task_id, completed=self._total)
            self._progress.stop()
            if message:
                console.print(f"[green]✓[/green] {message}")
    
    def error(self, message: str) -> None:
        """Report an error."""
        if self._progress:
            self._progress.stop()
        console.print(f"[red]✗[/red] {message}")


class SilentProgressReporter(ProgressReporter):
    """Silent progress reporter that does nothing."""
    
    def start(self, total: int, description: str = "") -> None:
        pass
    
    def update(self, current: int, message: str = "") -> None:
        pass
    
    def complete(self, message: str = "") -> None:
        pass
    
    def error(self, message: str) -> None:
        pass


def create_progress_reporter(silent: bool = False) -> ProgressReporter:
    """
    Create a progress reporter.
    
    Args:
        silent: If True, create a silent reporter
        
    Returns:
        ProgressReporter instance
    """
    if silent:
        return SilentProgressReporter()
    return RichProgressReporter()
