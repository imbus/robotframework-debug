*** Settings ***
Documentation       Library mode: a task imports RobotDebug and calls the
...                 ``Debug`` keyword. The shell opens at that point, can
...                 inspect variables / run keywords, and ``continue`` resumes
...                 the task.

Resource            ../resources/shell.resource

Force Tags          debug-keyword


*** Test Cases ***
Debug Keyword Opens The Shell And Continue Resumes
    ${input}=    Lines    continue
    ${out}=    Run Task In Debug Mode    debug_task.robot    ${input}
    Should Contain    ${out}    Enter interactive shell
    Should Contain    ${out}    post-debug-line

Inspect A Variable Defined Before Debug
    ${input}=    Lines
    ...    \${secret}
    ...    continue
    ${out}=    Run Task In Debug Mode    debug_task.robot    ${input}
    Should Contain    ${out}    \${secret} = 'pre-debug-value'

Run A Builtin Keyword Inside Debug
    ${input}=    Lines
    ...    Log To Console\tINSIDE_DEBUG_KEYWORD
    ...    continue
    ${out}=    Run Task In Debug Mode    debug_task.robot    ${input}
    Should Contain    ${out}    INSIDE_DEBUG_KEYWORD
    Should Contain    ${out}    post-debug-line

Call A User Keyword From The Resource Inside Debug
    ${input}=    Lines
    ...    Greet\tWorld
    ...    continue
    ${out}=    Run Task In Debug Mode    debug_task.robot    ${input}
    Should Contain    ${out}    hello-World

List Source With Longlist Inside Debug
    ${input}=    Lines
    ...    ll
    ...    continue
    ${out}=    Run Task In Debug Mode    debug_task.robot    ${input}
    Should Contain    ${out}    Debug Keyword Task
    Should Contain    ${out}    ->

List Source With List Inside Debug
    ${input}=    Lines
    ...    l
    ...    continue
    ${out}=    Run Task In Debug Mode    debug_task.robot    ${input}
    Should Contain    ${out}    Set Variable
