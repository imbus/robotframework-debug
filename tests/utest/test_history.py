"""Characterization tests for RobotDebug.history_app.get_history_content.

The history viewer splits stored entries into "commands" (plain keyword calls)
and "resources" (entries that start with a ``*** ... ***`` header), de-dupes
them and normalises separators. These tests lock that behaviour in.
"""

from RobotDebug import history_app as ha


class _FakeHistory:
    def __init__(self, items):
        self._items = items

    def get_strings(self):
        return list(self._items)


def test_commands_exclude_resource_headers_and_dedupe():
    his = _FakeHistory(
        [
            "Log    hi",
            "*** Keywords ***\nKw\n    Log    x",
            "Get Time",
            "Log    hi",  # duplicate
        ]
    )
    assert ha.get_history_content(his, pure_commands=True) == ["Get Time", "Log    hi"]


def test_resources_only_include_header_entries():
    his = _FakeHistory(
        [
            "Log    hi",
            "*** Keywords ***\nKw\n    Log    x",
        ]
    )
    assert ha.get_history_content(his, pure_commands=False) == [
        "*** Keywords ***\nKw\n    Log    x"
    ]


def test_separators_are_normalised_to_four_spaces():
    his = _FakeHistory(["Log\thi"])
    (entry,) = ha.get_history_content(his, pure_commands=True)
    assert "\t" not in entry
    assert "Log    hi" == entry
