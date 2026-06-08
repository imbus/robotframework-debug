"""Characterization tests for RobotDebug.robotkeyword.

These lock in the *current* behaviour of the pure-ish parsing/normalisation
helpers so the planned refactor of that module can be done safely.
"""

import pytest

from RobotDebug import robotkeyword as rk


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Log To Console", "logtoconsole"),
        ("Should_Be Equal", "shouldbeequal"),
        ("BuiltIn.Log", "builtin.log"),
        ("ALL CAPS KW", "allcapskw"),
    ],
)
def test_normalize_kw_strips_spaces_underscores_and_case(raw, expected):
    assert rk.normalize_kw(raw) == expected


def test_get_test_body_from_string_single_statement():
    test = rk.get_test_body_from_string("Log To Console\thello")
    assert len(test.body) == 1


def test_get_assignments_yields_assigned_variables():
    test = rk.get_test_body_from_string("${a}    ${b} =    Set Variable    1    2")
    # Current behaviour keeps the trailing "=" on the last assignment token.
    assert list(rk._get_assignments(test)) == ["${a}", "${b} ="]


def test_get_test_body_from_string_handles_multiline():
    body = "FOR    ${i}    IN    1    2\n    Log    ${i}\nEND"
    test = rk.get_test_body_from_string(body)
    assert len(test.body) == 1  # a single FOR structure
