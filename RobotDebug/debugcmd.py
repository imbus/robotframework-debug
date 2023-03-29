import difflib
import os
from typing import List

from prompt_toolkit.shortcuts import clear
from prompt_toolkit.styles import merge_styles
from robot.api import logger
from robot.errors import ExecutionFailed, HandlerExecutionFailed
from robot.libdocpkg.model import KeywordDoc
from robot.libraries.BuiltIn import BuiltIn
from robot.running.signalhandler import STOP_SIGNAL_MONITOR

from .cmdcompleter import CmdCompleter
from .globals import context
from .prompttoolkitcmd import PromptToolkitCmd
from .robotkeyword import find_keyword, get_keywords, get_lib_keywords, run_command
from .robotlib import get_builtin_libs, get_libs, match_libs
from .sourcelines import (
    RobotNeedUpgradeError,
    print_source_lines,
    print_test_case_lines,
)
from .steplistener import is_step_mode, set_step_mode
from .styles import (
    BASE_STYLE,
    DEBUG_PROMPT_STYLE,
    _get_print_style,
    get_debug_prompt_tokens,
    get_pygments_styles,
    get_style_by_name,
    print_error,
    print_output,
    style_from_pygments_cls,
)

HISTORY_PATH = os.environ.get("RFDEBUG_HISTORY", "~/.rfdebug_history")


def run_robot_command(robot_instance, command):
    """Run command in robotframewrk environment."""
    if not command:
        return

    result = []
    try:
        result = run_command(robot_instance, command)
    except HandlerExecutionFailed as exc:
        print_error("! FAIL:", exc.message)
    except ExecutionFailed as exc:
        print_error("! Expression:", command if "\n" not in command else f"\n{command}")
        print_error("! Execution error:", str(exc))
    except Exception as exc:
        print_error("! Expression:", command)
        print_error("! Error:", repr(exc))

    if result:
        for head, message in result:
            print_output(head, message)


class DebugCmd(PromptToolkitCmd):
    """Interactive debug shell for robotframework."""

    prompt_style = DEBUG_PROMPT_STYLE

    def __init__(self, completekey="tab", stdin=None, stdout=None):
        super().__init__(completekey, stdin, stdout, history_path=HISTORY_PATH)
        self.robot = BuiltIn()

    def get_prompt_tokens(self, prompt_text):
        return get_debug_prompt_tokens(prompt_text)

    def postcmd(self, stop, line):
        """Run after a command."""
        return stop

    def pre_loop_iter(self):
        """Reset robotframework before every loop iteration."""
        reset_robotframework_exception()

    def do_help(self, arg):
        """Show help message."""
        if not arg.strip():
            print(
                """\
Input Robotframework keywords, or commands listed below.
Use "libs" or "l" to see available libraries,
use "keywords" or "k" see the list of library keywords,
use the TAB keyboard key to autocomplete keywords.
Access https://github.com/imbus/robotframework-debug for more details.\
"""
            )
        super().do_help(arg)

    def get_completer(self):
        """Get completer instance specified for robotframework."""
        commands = [
            (cmd_name, cmd_name, f"DEBUG command: {doc}")
            for cmd_name, doc in self.get_helps()
        ]

        for lib in get_libs():
            commands.append(
                (
                    lib.name,
                    lib.name,
                    f"Library: {lib.name} {lib.version if hasattr(lib, 'version') else ''}",
                )
            )

        keywords: List[KeywordDoc] = get_keywords()
        for keyword in keywords:
            name = f"{keyword.parent.name}.{keyword.name}"
            commands.append(
                (
                    name,
                    keyword.name,
                    keyword.shortdoc,
                )
            )
            commands.append(
                (keyword.name, keyword.name, f"{keyword.shortdoc} [{keyword.parent.name}]")
            )

        return CmdCompleter(commands, self)

    def default(self, line):
        """Run RobotFramework keywords."""
        command = line.strip()

        run_robot_command(self.robot, command)

    def _print_lib_info(self, lib, with_source_path=False):
        print_output(f"   {lib.name}", lib.version if hasattr(lib, "version") else "")
        if lib.doc:
            doc = lib.doc.split('\n')[0]
            logger.console(f"       {doc}")
        if with_source_path:
            logger.console(f"       {lib.source}")

    def do_libs(self, args):
        """Print imported and builtin libraries, with source if `-s` specified.

        ls( libs ) [-s]
        """
        print_output("<", "Imported libraries:")
        for lib in get_libs():
            self._print_lib_info(lib, with_source_path="-s" in args)
        print_output("<", "Builtin libraries:")
        for name in sorted(get_builtin_libs()):
            print_output("   " + name, "")

    do_ls = do_libs

    def do_keywords(self, args):
        """Print keywords of libraries, all or starts with <lib_name>.

        k(eywords) [<lib_name>]
        """
        lib_name = args
        matched = match_libs(lib_name)
        if not matched:
            print_error("< not found library", lib_name)
            return
        for lib in matched:
            if lib:
                print_output("< Keywords of library", lib.name)
                for keyword in get_lib_keywords(lib):
                    print_output(f"   {keyword.name}\t", keyword.shortdoc)

    do_k = do_keywords

    def do_docs(self, keyword_name):
        """Get keyword documentation for individual keywords.

        d(ocs) [<keyword_name>]
        """

        keywords = find_keyword(keyword_name)
        if not keywords:
            print_error("< not find keyword", keyword_name)
        elif len(keywords) == 1:
            logger.console(keywords[0].doc)
        else:
            print_error(
                f"< found {len(keywords)} keywords", ", ".join([k.name for k in keywords])
            )

    do_d = do_docs

    def emptyline(self):
        """Repeat last nonempty command if in step mode."""
        self.repeat_last_nonempty_command = is_step_mode()
        return super().emptyline()

    def append_command(self, command):
        """Append a command to queue."""
        self.cmdqueue.append(command)

    def append_exit(self):
        """Append exit command to queue."""
        self.append_command("exit")

    def do_step(self, args):
        """Execute the current line, stop at the first possible occasion."""
        set_step_mode(on=True)
        self.append_exit()  # pass control back to robot runner

    do_s = do_step

    def do_next(self, args):
        """Continue execution until the next line is reached or it returns."""
        self.do_step(args)

    do_n = do_next

    def do_list(self, args):
        """List source code for the current file."""

        self.list_source(longlist=False)

    do_l = do_list

    def do_longlist(self, args):
        """List the whole source code for the current test case."""

        self.list_source(longlist=True)

    do_ll = do_longlist

    def list_source(self, longlist=False):
        """List source code."""
        if not is_step_mode():
            print("Please run `step` or `next` command first.")
            return

        print_function = print_test_case_lines if longlist else print_source_lines

        try:
            print_function(context.current_source_path, context.current_source_lineno)
        except RobotNeedUpgradeError:
            print("Please upgrade robotframework to support list source code:")
            print('    pip install "robotframework>=3.2" -U')

    def do_continue(self, args):
        """Continue execution."""
        return self.do_exit(args)

    def do_exit(self, args):
        """Exit debug shell."""
        set_step_mode(on=False)  # explicitly exit REPL will disable step mode
        self.append_exit()
        return super().do_exit(args)

    do_c = do_continue

    def onecmd(self, line):
        # restore last command acrossing different Cmd instances
        self.lastcmd = context.last_command
        stop = super().onecmd(line)
        context.last_command = self.lastcmd
        return stop

    def do_style(self, args):
        """Set style of output. Usage `style    <style_name>`. Call just `style` to list all styles."""
        styles = get_pygments_styles()
        if not args.strip():
            for style in styles:
                print_output(f"> {style}    ", style, _get_print_style(style))
            return
        style = difflib.get_close_matches(args.strip(), styles)[0]
        self.prompt_style = merge_styles(
            [BASE_STYLE, style_from_pygments_cls(get_style_by_name(style))]
        )
        print_output("Set style to:   ", style, _get_print_style(str(style)))

    def do_clear(self, args):
        """Clear screen."""
        clear()

    do_cls = do_clear


def reset_robotframework_exception():
    """Resume RF after press ctrl+c during keyword running."""
    if STOP_SIGNAL_MONITOR._signal_count:
        STOP_SIGNAL_MONITOR._signal_count = 0
        STOP_SIGNAL_MONITOR._running_keyword = True
        logger.info("Reset last exception of DebugLibrary")
