*** Settings ***
Documentation       Interactive ``irobot`` shell (REPL mode): running keywords,
...                 assigning and displaying variables, fail-safety and the
...                 nested ``Debug If`` shell.

Resource            ../resources/shell.resource

Force Tags          repl


*** Test Cases ***
Run A Library Keyword
    ${input}=    Lines
    ...    Log To Console\tHELLO_FROM_REPL
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Enter interactive shell
    Should Contain    ${out}    HELLO_FROM_REPL
    Should Contain    ${out}    Exit shell.

Keyword Return Value Is Printed
    ${input}=    Lines
    ...    Evaluate\t6 * 7
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    < 42

Scalar Variable Assignment And Display
    ${input}=    Lines
    ...    \${name} =\tSet Variable\tadmin
    ...    \${name}
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    \${name} = 'admin'

List Variable Assignment And Display
    ${input}=    Lines
    ...    \@{items} =\tCreate List\thello\tworld
    ...    \@{items}
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    ['hello', 'world']

Dictionary Variable Assignment And Member Access
    ${input}=    Lines
    ...    \&{user} =\tCreate Dictionary\tname=admin\trole=root
    ...    \${user.name}
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    admin

Failing Keyword Does Not Crash The Shell
    ${input}=    Lines
    ...    Fail\tboom-in-repl
    ...    Log To Console\tSHELL_STILL_ALIVE
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    boom-in-repl
    Should Contain    ${out}    SHELL_STILL_ALIVE

Unknown Keyword Does Not Crash The Shell
    ${input}=    Lines
    ...    This Keyword Does Not Exist At All
    ...    Log To Console\tSURVIVED_UNKNOWN
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    SURVIVED_UNKNOWN

Nested Debug Opens A Second Shell
    # Calling Debug from inside the shell opens a nested shell. Counting the
    # banners avoids a false positive from the outer shell echoing the marker.
    ${input}=    Lines
    ...    Debug
    ...    Log To Console\tINSIDE_NESTED_DEBUG
    ...    continue
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    INSIDE_NESTED_DEBUG
    ${shells}=    Get Count    ${out}    Enter interactive shell
    Should Be True    ${shells} >= 2

Multiple Keywords On Separate Lines
    ${input}=    Lines
    ...    Log To Console\tFIRST_LINE
    ...    Log To Console\tSECOND_LINE
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    FIRST_LINE
    Should Contain    ${out}    SECOND_LINE
