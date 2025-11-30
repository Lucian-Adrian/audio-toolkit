"""
Sample Audio Toolkit Plugin

This is an example plugin demonstrating how to create third-party
processors for Audio Toolkit.

Installation:
    pip install -e tests/fixtures/sample_plugin/

After installation, the EchoProcessor will appear in:
    audiotoolkit plugins list
"""

from .echo_processor import EchoProcessor

__version__ = "0.1.0"
__all__ = ["EchoProcessor"]
