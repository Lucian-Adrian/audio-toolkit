"""Progress reporting utilities."""

import sys
from typing import Optional
from ..core.interfaces import ProgressReporter
from .logger import logger


class ConsoleProgressReporter(ProgressReporter):
    """Console-based progress reporter."""

    def __init__(self, show_percentage: bool = True):
        self.show_percentage = show_percentage
        self.total_steps = 0
        self.description = ""

    def start(self, total_steps: int, description: str = ""):
        """Start progress reporting."""
        self.total_steps = total_steps
        self.description = description
        if description:
            print(f"Starting: {description}")
        self._print_progress(0)

    def update(self, current_step: int):
        """Update progress."""
        if self.total_steps > 0:
            progress = int((current_step / self.total_steps) * 100)
            self._print_progress(progress)

    def complete(self):
        """Mark progress as complete."""
        self._print_progress(100)
        print("Complete!")

    def _print_progress(self, percentage: int):
        """Print progress to console."""
        if self.show_percentage:
            bar = self._create_progress_bar(percentage)
            print(f"\r{bar} {percentage}%", end="", flush=True)
        else:
            print(".", end="", flush=True)

    def _create_progress_bar(self, percentage: int, width: int = 50) -> str:
        """Create a progress bar string."""
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"


class SilentProgressReporter(ProgressReporter):
    """Silent progress reporter that does nothing."""

    def start(self, total_steps: int, description: str = ""):
        pass

    def update(self, current_step: int):
        pass

    def complete(self):
        pass


def get_progress_reporter(use_console: bool = True) -> ProgressReporter:
    """Get a progress reporter instance."""
    if use_console:
        return ConsoleProgressReporter()
    else:
        return SilentProgressReporter()