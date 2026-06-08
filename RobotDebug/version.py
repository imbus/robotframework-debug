"""Backwards-compatible version export.

The single source of truth is ``RobotDebug.__version__`` (read by Flit at
build time). This module keeps the historical ``VERSION`` name working.
"""

from RobotDebug import __version__ as VERSION  # noqa: F401
