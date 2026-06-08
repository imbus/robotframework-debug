"""Characterization tests for RobotDebug.globals."""

from RobotDebug import globals as g


def test_step_mode_values():
    assert {m.value for m in g.StepMode} == {
        "_INTO",
        "_OVER",
        "_OUT",
        "_CONTINUE",
        "_STOP",
    }


def test_keyword_sep_splits_on_two_spaces_or_tab():
    assert g.KEYWORD_SEP.split("Log To Console\tvalue   two") == [
        "Log To Console",
        "value",
        "two",
    ]
    # A single space inside a value is NOT a separator.
    assert g.KEYWORD_SEP.split("Log To Console") == ["Log To Console"]


def test_is_rf_7_is_a_bool():
    assert isinstance(g.IS_RF_7, bool)


def test_context_holds_mutable_shared_state():
    # The module-level ``context`` is the single shared state object.
    g.context.in_step_mode = True
    g.context.last_command = "Log    hi"
    assert g.context.in_step_mode is True
    assert g.context.last_command == "Log    hi"
    g.context.in_step_mode = False
    g.context.last_command = ""
