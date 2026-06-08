"""Robot Framework helper library for the RobotDebug acceptance tests.

It does only the things that are awkward to do in pure Robot syntax:

* build the exact command lines for the ``irobot`` shell and for ``robot``
  running a task fixture (using the *same* interpreter that runs the tests),
* turn a human readable input script into the raw bytes that are piped to the
  shell's stdin -- including the function-key escape sequences used for step
  debugging,
* strip ANSI escape sequences / carriage returns from the captured output so
  the suites can assert on plain text.

The actual process interaction is done in Robot with the standard ``Process``
library (see ``resources/shell.resource``); this module only prepares input
and cleans output.
"""

from __future__ import annotations

import re
import sys
import tempfile

# Escape sequences emitted by the terminal for the keys RobotDebug binds for
# step debugging. Tests use the readable ``<F8>`` placeholders instead.
FUNCTION_KEYS = {
    "<F7>": "\x1b[18~",   # INTO
    "<F8>": "\x1b[19~",   # OVER
    "<F9>": "\x1b[20~",   # OUT
    "<F10>": "\x1b[21~",  # CONTINUE
    "<STAB>": "\x1b[Z",   # SHIFT-TAB / DETACH
}

# CSI / OSC / charset-select escape sequences produced by prompt_toolkit.
_ANSI = re.compile(
    r"\x1b\[[0-9;?]*[ -/]*[@-~]"   # CSI ... final byte
    r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"  # OSC ... BEL / ST
    r"|\x1b[=>()][0-9A-Za-z]?"      # charset / keypad mode
)

# Arguments that silence all of Robot Framework's report/log/output writing so
# only the shell interaction shows up on stdout.
NO_OUTPUT = ["--output", "NONE", "--report", "NONE", "--log", "NONE",
             "--xunit", "NONE", "--quiet"]


class DebugShell:
    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def get_interpreter(self) -> str:
        """Absolute path of the Python interpreter running the tests."""
        return sys.executable

    def repl_command(self, *extra: str) -> list[str]:
        """Command line that launches the standalone ``irobot`` shell."""
        return [sys.executable, "-m", "RobotDebug.shell", *extra]

    def robot_task_command(self, task: str, listener: str = "") -> list[str]:
        """Command line that runs ``robot`` against a task fixture.

        When *listener* is given (e.g. ``RobotDebug.Listener``) it is attached
        so the shell opens automatically on the first failure.
        """
        cmd = [sys.executable, "-m", "robot", *NO_OUTPUT]
        if listener:
            cmd += ["--listener", listener]
        cmd.append(task)
        return cmd

    def write_stdin_file(self, script: str) -> str:
        """Expand ``<F8>`` style placeholders and write *script* to a temp file.

        Returns the path, suitable for ``Run Process    ...    stdin=${path}``.
        """
        for placeholder, sequence in FUNCTION_KEYS.items():
            script = script.replace(placeholder, sequence)
        handle = tempfile.NamedTemporaryFile(
            mode="w", prefix="rfdebug_stdin_", suffix=".txt",
            encoding="utf-8", delete=False,
        )
        handle.write(script)
        handle.close()
        return handle.name

    def clean_output(self, text: str) -> str:
        """Remove ANSI escape sequences and carriage returns from *text*."""
        if text is None:
            return ""
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="replace")
        text = _ANSI.sub("", text)
        return text.replace("\r", "")
