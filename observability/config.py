"""Backward-compatibility wrapper re-exporting logging utilities."""

from observability.logging import JSONLogFormatter, setup_logging

__all__ = ["JSONLogFormatter", "setup_logging"]
