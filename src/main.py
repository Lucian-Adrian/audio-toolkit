"""Main entry point for the Audio Toolkit CLI."""

from .presentation.cli import app

# Export app for use as entry point
__all__ = ["app"]


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
