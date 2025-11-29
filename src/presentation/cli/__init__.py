"""Command-line interface for the audio toolkit."""

import click
from ...utils.config import config_manager
from ...utils.logger import setup_logger
from .convert_cmd import convert_cmd
from .split_cmd import split_cmd


@click.group()
@click.option('--log-level', default='INFO', help='Logging level')
@click.option('--log-file', type=click.Path(), help='Log file path')
def cli(log_level, log_file):
    """Audio Toolkit CLI"""
    # Setup logging
    level = getattr(__import__('logging'), log_level.upper(), 20)
    setup_logger(level=level, log_file=log_file if log_file else None)


cli.add_command(convert_cmd)
cli.add_command(split_cmd)


if __name__ == '__main__':
    cli()