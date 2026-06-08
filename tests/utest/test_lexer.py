"""Characterization tests for RobotDebug.lexer.

The lexer wraps RF's tokenizer and uses a 20-char indent marker so a single
REPL line can be tokenized as if it were inside a test case. These tests pin
that behaviour down before the module is refactored.
"""

from RobotDebug import lexer as lx


def _types_and_values(line):
    return [(str(t.type), t.value) for t in lx.get_robot_token(line)]


def test_get_robot_token_strips_the_indent_marker():
    toks = _types_and_values("Log To Console\thello")
    # The synthetic 20-space indent must not leak into the produced tokens.
    assert toks[0] == ("KEYWORD", "Log To Console")
    assert ("ARGUMENT", "hello") in toks
    assert all(not v.startswith(" " * 20) for _, v in toks)


def test_header_matcher_matches_section_headers():
    assert lx.HEADER_MATCHER.match("*** Keywords ***")
    assert lx.HEADER_MATCHER.match("*** Settings ***")
    assert lx.HEADER_MATCHER.match("  *** Variables ***")


def test_header_matcher_rejects_plain_keywords():
    assert not lx.HEADER_MATCHER.match("Log To Console")
    assert not lx.HEADER_MATCHER.match("${var}")


def test_get_robot_token_passes_headers_through():
    toks = _types_and_values("*** Keywords ***")
    assert any("HEADER" in t for t, _ in toks)


def test_get_variable_token_tokenizes_variables_in_arguments():
    # Build a token whose value embeds a variable, then split it.
    [kw_token, *_] = list(lx.get_robot_token("Log\t${name}"))
    arg_tokens = list(lx.get_robot_token("Log\t${name}"))
    var_tokens = list(lx.get_variable_token(arg_tokens))
    # The ${name} variable should be surfaced as its own token value somewhere.
    assert any("${name}" in t.value for t in var_tokens)
