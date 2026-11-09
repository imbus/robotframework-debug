*** Settings ***
Documentation       Listener mode: ``robot --listener RobotDebug.Listener``.
...                 The shell opens automatically when a keyword fails, shows
...                 the failing source line and lets you inspect state before
...                 ``continue`` lets the failure propagate.

Resource            ../resources/shell.resource

Force Tags          listener


*** Test Cases ***
Shell Opens Automatically On Failure
    ${input}=    Lines
    ...    Log To Console\tINSIDE_ERROR_SHELL
    ...    continue
    ${out}=    Run Task In Listener Mode    error_task.robot    ${input}
    Should Contain    ${out}    before-failure
    Should Contain    ${out}    INSIDE_ERROR_SHELL

Failure Message Is Shown
    ${input}=    Lines    continue
    ${out}=    Run Task In Listener Mode    error_task.robot    ${input}
    Should Contain    ${out}    boom-intentional-failure

Failing Source Line Is Highlighted
    ${input}=    Lines    continue
    ${out}=    Run Task In Listener Mode    error_task.robot    ${input}
    Should Contain    ${out}    error_task.robot
    Should Contain    ${out}    ->
    Should Contain    ${out}    Should Be Equal

Variables Can Be Inspected At The Point Of Failure
    # Assert on the variable-display form so a source listing that merely
    # mentions the task name cannot satisfy the check.
    ${input}=    Lines
    ...    \${TEST_NAME}
    ...    continue
    ${out}=    Run Task In Listener Mode    error_task.robot    ${input}
    Should Contain    ${out}    \${TEST_NAME} = 'Failing Task'

Execution Does Not Continue Past The Failed Keyword
    # The marker only appears in the source listing as the literal
    # "${UNREACHED_MARKER}"; its resolved value must never be printed.
    ${input}=    Lines    continue
    ${out}=    Run Task In Listener Mode    error_task.robot    ${input}
    Should Not Contain    ${out}    SENTINEL_THAT_RAN

Shell Shows Context When The Library Is Also Imported
    [Documentation]    Regression for C1: importing "Library RobotDebug" used to
    ...    re-run __init__ and reset the listener wiring, so the on-failure shell
    ...    opened with no banner and no source context. It must still show them.
    ${input}=    Lines    continue
    ${out}=    Run Task In Listener Mode    error_with_library.robot    ${input}
    Should Contain    ${out}    error_with_library.robot
    Should Contain    ${out}    ->
    Should Contain    ${out}    boom-with-library
