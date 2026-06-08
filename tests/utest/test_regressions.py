"""Regression tests for the Phase 2 bug fixes (C1, C2, C3).

These previously lived in test_known_issues.py as ``xfail`` markers; the fixes
in this phase turn them into passing guards. See docs/code_review.md.
"""

import pytest
from prompt_toolkit.document import Document

from RobotDebug.cmdcompleter import CmdCompleter
from RobotDebug.debugcmd import ReplCmd
from RobotDebug.RobotDebug import Listener, RobotDebug


@pytest.fixture
def _reset_singletons():
    """Reset the module-level singletons so the test is isolated."""
    RobotDebug._instance = None
    Listener.instance = None
    yield
    RobotDebug._instance = None
    Listener.instance = None


def test_robotdebug_singleton_preserves_state_across_calls(_reset_singletons):
    """C1: __init__ must run once; a later bare construction must not reset state."""
    first = RobotDebug(repl=True)
    second = RobotDebug()  # e.g. a `Library RobotDebug` import after the listener
    assert first is second
    assert second.is_repl is True


class _FakeLib:
    cli_listener = False
    ROBOT_LIBRARY_LISTENER = None
    is_repl = True


def test_do_style_with_unknown_name_does_not_crash():
    """C2: an unknown style name reports an error instead of raising IndexError."""
    cmd = ReplCmd(_FakeLib())
    cmd.do_style("definitely-not-a-real-style-name")  # must not raise


def test_completer_without_repl_does_not_crash():
    """C3: a completer built without a repl must not dereference None."""
    completer = CmdCompleter([], [], [], None)
    # Should compute (empty) completions without an AttributeError.
    assert list(completer.get_completions(Document("Log"), None)) == []
