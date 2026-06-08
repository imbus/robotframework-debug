*** Settings ***
Documentation       High-level keywords that drive the RobotDebug interactive
...                 shell. The interaction itself uses the standard Process
...                 library; ``DebugShell.py`` only prepares the piped stdin
...                 (incl. function-key escape sequences) and cleans ANSI noise
...                 out of the captured output.

Library             Process
Library             OperatingSystem
Library             ${CURDIR}/../DebugShell.py


*** Variables ***
${FIXTURES}         ${CURDIR}/../fixtures
${TIMEOUT}          45s


*** Keywords ***
Run Interactive Shell
    [Documentation]    Launch ``irobot`` (REPL mode), pipe ${input} to its
    ...    stdin and return the cleaned, combined stdout/stderr.
    [Arguments]    ${input}    @{extra_args}
    @{cmd}=    Repl Command    @{extra_args}
    ${output}=    Drive Shell    ${cmd}    ${input}
    RETURN    ${output}

Run Task In Debug Mode
    [Documentation]    Run a task fixture under ``robot`` (Library mode: the
    ...    fixture imports RobotDebug and calls Debug / steps).
    [Arguments]    ${task}    ${input}
    @{cmd}=    Robot Task Command    ${FIXTURES}/${task}
    ${output}=    Drive Shell    ${cmd}    ${input}
    RETURN    ${output}

Run Task In Listener Mode
    [Documentation]    Run a task fixture under ``robot`` with the RobotDebug
    ...    listener attached, so the shell opens on the first failure.
    [Arguments]    ${task}    ${input}
    @{cmd}=    Robot Task Command    ${FIXTURES}/${task}    listener=RobotDebug.Listener
    ${output}=    Drive Shell    ${cmd}    ${input}
    RETURN    ${output}

Lines
    [Documentation]    Join command lines with newlines (and a trailing newline)
    ...    into a single stdin script. Use a literal tab (\t) inside a line to
    ...    separate a keyword from its arguments.
    [Arguments]    @{lines}
    ${script}=    Evaluate    "\\n".join($lines) + "\\n"
    RETURN    ${script}

Drive Shell
    [Documentation]    Write ${input} to a temp file, run ${cmd} with that file
    ...    as stdin (stderr merged into stdout), and return cleaned output.
    [Arguments]    ${cmd}    ${input}
    ${stdin_file}=    Write Stdin File    ${input}
    ${result}=    Run Process    @{cmd}
    ...    stdin=${stdin_file}    stderr=STDOUT    timeout=${TIMEOUT}    cwd=${CURDIR}/../../..
    ${output}=    Clean Output    ${result.stdout}
    Log    ${output}
    Remove File    ${stdin_file}
    RETURN    ${output}
