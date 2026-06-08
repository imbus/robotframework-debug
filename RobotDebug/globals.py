import re
from enum import Enum

from robot.version import get_version


class _Context:
    """Mutable shell-wide state, shared through the module-level ``context``."""

    def __init__(self):
        self.in_step_mode = False
        self.last_command = ""


context = _Context()


class StepMode(str, Enum):
    INTO = "_INTO"
    OVER = "_OVER"
    OUT = "_OUT"
    CONTINUE = "_CONTINUE"
    STOP = "_STOP"


IS_RF_7 = int(get_version().split(".", 1)[0]) >= 7  # noqa: PLR2004
KEYWORD_SEP = re.compile(r"[ \t]{2,}|\t")
