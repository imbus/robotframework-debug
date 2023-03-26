import re

from prompt_toolkit.completion import Completer, Completion
from pygments.lexer import Lexer
from pygments.token import Token
from robot.parsing.lexer import get_tokens

from .robotkeyword import normalize_kw, parse_keyword
from .styles import _get_style_completions


class CmdCompleter(Completer):
    """Completer for debug shell."""

    def __init__(self, commands, cmd_repl=None):
        self.names = []
        self.displays = {}
        self.display_metas = {}
        for name, display, display_meta in commands:
            self.names.append(name)
            self.displays[name] = display
            self.display_metas[name] = display_meta
        self.cmd_repl = cmd_repl

    def _get_argument_completions(self, completer, document):
        """Using Cmd.py's completer to complete arguments."""
        end_idx = document.cursor_position_col
        line = document.current_line
        if line[:end_idx].rfind(" ") >= 0:
            begin_idx = line[:end_idx].rfind(" ") + 1
        else:
            begin_idx = 0
        prefix = line[begin_idx:end_idx]

        completions = completer(prefix, line, begin_idx, end_idx)
        for comp in completions:
            yield Completion(comp, begin_idx - end_idx, display=comp)

    def _get_custom_completions(self, cmd_name, document):
        completer = getattr(
            self.cmd_repl,
            "complete_{0}".format(cmd_name),
            None,
        )
        if completer:
            yield from self._get_argument_completions(completer, document)

    def _get_command_completions(self, text):
        content = text.strip().split("  ")[-1].lower().strip()
        suffix_len = len(text) - len(text.rstrip())
        return (
            Completion(
                f"{name}{' ' * suffix_len}",
                -len(content),
                display=self.displays.get(name, ""),
                display_meta=self.display_metas.get(name, ""),
            )
            for name in self.names
            if (
                (
                    ("." not in name and "." not in text)  # root level
                    or ("." in name and "." in text)
                )  # library level
                and normalize_kw(name).startswith(normalize_kw(content))
            )
        )

    def _get_resource_completions(self, text):
        return (
            Completion(
                name,
                -len(text.lstrip()),
                display=name,
                display_meta="",
            )
            for name in [
                "*** Settings ***",
                "*** Variables ***",
                "*** Keywords ***",
            ]
            if (name.lower().strip().startswith(text.strip()))
        )

    def get_completions(self, document, complete_event):
        """Compute suggestions."""
        # RobotFrameworkLocalLexer().parse_doc(document)
        text = document.current_line_before_cursor
        variables, keyword, args = parse_keyword(text.strip())
        if "FOR".startswith(text):
            yield from [
                Completion(
                    "FOR    ${var}    IN    @{list}\n    Log    ${var}\nEND",
                    -len(text),
                    display="FOR IN",
                    display_meta="For-Loop over all items in a list",
                ),
                Completion(
                    "FOR    ${var}    IN RANGE    5\n    Log    ${var}\nEND",
                    -len(text),
                    display="FOR IN RANGE",
                    display_meta="For-Loop over a range of numbers",
                ),
                Completion(
                    "FOR    ${index}    ${var}    IN ENUMERATE"
                    "    @{list}\n    Log    ${index} - ${var}n\nEND",
                    -len(text),
                    display="FOR IN ENUMERATE",
                    display_meta="For-Loop over all items in a list with index",
                ),
            ]
        elif "IF".startswith(text):
            yield from [
                Completion(
                    "IF    <py-eval>    Log    None",
                    -len(text),
                    display="IF (one line)",
                    display_meta="If-Statement as one line",
                ),
                Completion(
                    "IF    <py-eval>\n    Log    if-branche\nEND",
                    -len(text),
                    display="IF (multi line)",
                    display_meta="If-Statement as multi line",
                ),
            ]
        elif re.fullmatch(r"style {2,}.*", text):
            yield from _get_style_completions(text.lower())
        elif text.startswith("*"):
            yield from self._get_resource_completions(text.lower())
        elif keyword:
            if not args:
                yield from self._get_command_completions(text.lower())

            # yield from self._get_custom_completions(keyword, document)


class RobotFrameworkLocalLexer(Lexer):
    name = "RobotFramework"
    url = "http://robotframework.org"
    aliases = ["robotframework"]
    filenames = ["*.robot", "*.resource"]
    mimetypes = ["text/x-robotframework"]

    # PYGMENTS_STANDARD_TYPES = {
    #     Token: '',
    #
    #     Text: '',
    #     Whitespace: 'w',
    #     Escape: 'esc',
    #     Error: 'err',
    #     Other: 'x',
    #
    #     Keyword: 'k',
    #     Keyword.Constant: 'kc',
    #     Keyword.Declaration: 'kd',
    #     Keyword.Namespace: 'kn',
    #     Keyword.Pseudo: 'kp',
    #     Keyword.Reserved: 'kr',
    #     Keyword.Type: 'kt',
    #
    #     Name: 'n',
    #     Name.Attribute: 'na',
    #     Name.Builtin: 'nb',
    #     Name.Builtin.Pseudo: 'bp',
    #     Name.Class: 'nc',
    #     Name.Constant: 'no',
    #     Name.Decorator: 'nd',
    #     Name.Entity: 'ni',
    #     Name.Exception: 'ne',
    #     Name.Function: 'nf',
    #     Name.Function.Magic: 'fm',
    #     Name.Property: 'py',
    #     Name.Label: 'nl',
    #     Name.Namespace: 'nn',
    #     Name.Other: 'nx',
    #     Name.Tag: 'nt',
    #     Name.Variable: 'nv',
    #     Name.Variable.Class: 'vc',
    #     Name.Variable.Global: 'vg',
    #     Name.Variable.Instance: 'vi',
    #     Name.Variable.Magic: 'vm',
    #
    #     Literal: 'l',
    #     Literal.Date: 'ld',
    #
    #     String: 's',
    #     String.Affix: 'sa',
    #     String.Backtick: 'sb',
    #     String.Char: 'sc',
    #     String.Delimiter: 'dl',
    #     String.Doc: 'sd',
    #     String.Double: 's2',
    #     String.Escape: 'se',
    #     String.Heredoc: 'sh',
    #     String.Interpol: 'si',
    #     String.Other: 'sx',
    #     String.Regex: 'sr',
    #     String.Single: 's1',
    #     String.Symbol: 'ss',
    #
    #     Number: 'm',
    #     Number.Bin: 'mb',
    #     Number.Float: 'mf',
    #     Number.Hex: 'mh',
    #     Number.Integer: 'mi',
    #     Number.Integer.Long: 'il',
    #     Number.Oct: 'mo',
    #
    #     Operator: 'o',
    #     Operator.Word: 'ow',
    #
    #     Punctuation: 'p',
    #     Punctuation.Marker: 'pm',
    #
    #     Comment: 'c',
    #     Comment.Hashbang: 'ch',
    #     Comment.Multiline: 'cm',
    #     Comment.Preproc: 'cp',
    #     Comment.PreprocFile: 'cpf',
    #     Comment.Single: 'c1',
    #     Comment.Special: 'cs',
    #
    #     Generic: 'g',
    #     Generic.Deleted: 'gd',
    #     Generic.Emph: 'ge',
    #     Generic.Error: 'gr',
    #     Generic.Heading: 'gh',
    #     Generic.Inserted: 'gi',
    #     Generic.Output: 'go',
    #     Generic.Prompt: 'gp',
    #     Generic.Strong: 'gs',
    #     Generic.Subheading: 'gu',
    #     Generic.Traceback: 'gt',
    # }

    ROBOT_TO_PYGMENTS = {
        "SETTING HEADER": Token.Generic.Heading,
        "VARIABLE HEADER": Token.Generic.Heading,
        "TESTCASE HEADER": Token.Generic.Heading,
        "TASK HEADER": Token.Generic.Heading,
        "KEYWORD HEADER": Token.Generic.Heading,
        "COMMENT HEADER": Token.Generic.Heading,
        "TESTCASE NAME": Token.Name.Class,
        "KEYWORD NAME": Token.Name.Class,
        "DOCUMENTATION": Token.Name.Attribute,
        "SUITE SETUP": Token.Name.Attribute,
        "SUITE TEARDOWN": Token.Name.Attribute,
        "METADATA": Token.Name.Attribute,
        "TEST SETUP": Token.Name.Attribute,
        "TEST TEARDOWN": Token.Name.Attribute,
        "TEST TEMPLATE": Token.Name.Attribute,
        "TEST TIMEOUT": Token.Name.Attribute,
        "FORCE TAGS": Token.Name.Attribute,
        "DEFAULT TAGS": Token.Name.Attribute,
        "KEYWORD TAGS": Token.Name.Attribute,
        "LIBRARY": Token.Name.Attribute,
        "RESOURCE": Token.Name.Attribute,
        "VARIABLES": Token.Name.Attribute,
        "SETUP": Token.Keyword.Namespace,
        "TEARDOWN": Token.Keyword.Namespace,
        "TEMPLATE": Token.Keyword.Namespace,
        "TIMEOUT": Token.Keyword.Namespace,
        "TAGS": Token.Keyword.Namespace,
        "ARGUMENTS": Token.Keyword.Namespace,
        "RETURN_SETTING": Token.Keyword.Namespace,
        "NAME": Token.Name,
        "VARIABLE": Token.Name.Variable,
        "ARGUMENT": Token.String,
        "ASSIGN": Token.Name.Variable,
        "KEYWORD": Token.Name.Function,
        "WITH NAME": Token.Keyword,
        "FOR": Token.Keyword,
        "FOR SEPARATOR": Token.Keyword,
        "END": Token.Keyword,
        "IF": Token.Keyword,
        "INLINE IF": Token.Keyword,
        "ELSE IF": Token.Keyword,
        "ELSE": Token.Keyword,
        "TRY": Token.Keyword,
        "EXCEPT": Token.Keyword,
        "FINALLY": Token.Keyword,
        "AS": Token.Keyword,
        "WHILE": Token.Keyword,
        "RETURN STATEMENT": Token.Keyword,
        "CONTINUE": Token.Keyword,
        "BREAK": Token.Keyword,
        "OPTION": Token.Keyword,
        "SEPARATOR": Token.Punctuation,
        "COMMENT": Token.Comment,
        "CONTINUATION": Token.Operator,
        "CONFIG": Token.Punctuation,
        "EOL": Token.Punctuation,
        "EOS": Token.Punctuation,
        "ERROR": Token.Error,
        "FATAL ERROR": Token.Error,
    }

    def __init__(self, **options):
        options["tabsize"] = 2
        options["encoding"] = "UTF-8"
        Lexer.__init__(self, **options)

    # def parse_doc(self, document):
    #     text = document.text
    #     cursor_col = document.cursor_position_col
    #     cursor_row = document.cursor_position_row
    #     doc_tokens = list(Tokenizer().tokenize(text))
    #     # statements = _tokens_to_statements(tok)
    #     statement_at_cursor, token_at_cursor = self.tokenize_statement(cursor_col, cursor_row, doc_tokens)
    #     pygments_tokens = list(RobotFrameworkLexer().get_tokens_unprocessed(text))
    #     return doc_tokens, statement_at_cursor, token_at_cursor
    #
    # def tokenize_statement(self, cursor_col, cursor_row, doc_tokens):
    #     statement_at_cursor = None
    #     token_at_cursor = None
    #     for statement in doc_tokens:
    #         content_token = [token for token in statement if token.type not in ["SEPARATOR", "EOL", "CONTINUATION"]]
    #         kwl = KeywordCallLexer(ResourceFileContext())
    #         kwl.input(content_token)
    #         kwl._lex_as_keyword_call()
    #         if not token_at_cursor:
    #             for token in statement:
    #                 if token.lineno - 1 == cursor_row:
    #                     if token.col_offset <= cursor_col < token.end_col_offset:
    #                         token_at_cursor = token
    #                         statement_at_cursor = statement
    #                         break
    #     return statement_at_cursor, token_at_cursor

    def get_robot_token(self, text):
        if text.strip().startswith("**"):
            yield from get_tokens(text)
        else:
            marker_len = 20
            new_line_start = " " * marker_len
            if "\n" in text:
                text = f"\n{new_line_start}".join(text.split("\n"))
            suite_str = f"*** Test Cases ***\nFake Test\n{new_line_start}{text}"
            for token in list(get_tokens(suite_str))[6:]:
                if (
                    token.type in ["SEPARATOR", "EOL"]
                    and token.col_offset == 0
                    and token.end_col_offset >= marker_len
                ):
                    if token.end_col_offset == marker_len:
                        continue
                    token.value = token.value[marker_len:]
                    token.col_offset = 0
                    token.lineno = token.lineno - 2
                else:
                    token.col_offset = token.col_offset - marker_len
                    token.lineno = token.lineno - 2
                yield token

    def get_tokens_unprocessed(self, text):
        token_list = self.get_robot_token(text)
        index = 0
        for token in token_list:
            if len(token.value) == 0:
                continue
            yield index, self.ROBOT_TO_PYGMENTS.get(token.type, Token.Generic.Error), token.value
            index += len(token.value)
