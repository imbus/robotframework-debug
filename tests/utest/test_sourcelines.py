"""Characterization tests for RobotDebug.sourcelines token helpers.

Covers the line-number prefixing and line-range filtering used by the
``list``/``longlist`` commands, so the planned removal of the dead
``_find_*``/``_print_lines`` helpers and any refactor of the live token path
can be verified.
"""

from pygments.token import Token

from RobotDebug import sourcelines as sl

T = Token.Text
_TOKENS = [(T, "a"), (T, "\n"), (T, "b"), (T, "\n"), (T, "c")]


def test_prefix_line_numbers_adds_one_marker_per_line():
    out = list(sl.prefix_line_numbers_and_position(_TOKENS, lineno=2))
    line_no_values = [v for t, v in out if t == sl.LINE_NO_TOKEN]
    assert line_no_values == ["  1   ", "  2 ->", "  3   "]


def test_prefix_line_numbers_marks_the_current_line_with_arrow():
    out = list(sl.prefix_line_numbers_and_position(_TOKENS, lineno=3))
    arrowed = [v for t, v in out if t == sl.LINE_NO_TOKEN and "->" in v]
    assert arrowed == ["  3 ->"]


def test_filter_token_by_lineno_keeps_only_the_requested_range():
    out = list(sl.prefix_line_numbers_and_position(_TOKENS, lineno=2))
    kept = [v for t, v in sl.filter_token_by_lineno(out, 2, 3) if t != sl.LINE_NO_TOKEN]
    assert kept == ["b", "\n"]


def test_filter_token_by_lineno_empty_range_yields_nothing():
    out = list(sl.prefix_line_numbers_and_position(_TOKENS, lineno=1))
    assert list(sl.filter_token_by_lineno(out, 10, 12)) == []
