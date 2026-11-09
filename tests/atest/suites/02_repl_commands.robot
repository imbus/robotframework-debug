*** Settings ***
Documentation       Every interactive ``irobot`` shell meta command and its
...                 aliases/flags: libs[ -s], res[ -s], keywords/k, docs/d,
...                 style, clear/cls, help and the ``?`` help prefix.
...
...                 ``keywords``/``k`` and ``docs``/``d`` build library keyword
...                 documentation, which used to break on Robot Framework 7.4.x
...                 (removed ``LibraryDocBuilder._get_type_docs``); see the
...                 compatibility matrix and ``RobotDebug/robotlib.py``.

Resource            ../resources/shell.resource

Force Tags          repl    commands


*** Test Cases ***
List Imported Libraries
    ${input}=    Lines    libs    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Imported libraries:
    Should Contain    ${out}    BuiltIn
    Should Contain    ${out}    RobotDebug

List Imported Libraries With Source
    ${input}=    Lines    libs -s    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Imported libraries:
    # -s adds the source path of each library.
    Should Contain    ${out}    BuiltIn.py

List Imported Resources
    ${input}=    Lines    res    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Imported resources:

List Imported Resources With Source
    ${input}=    Lines    res -s    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Imported resources:

List Keywords Of A Library
    [Tags]    libdoc
    ${input}=    Lines
    ...    keywords\tRobotDebug
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Keywords of library RobotDebug
    # "Variables" is a RobotDebug keyword and, unlike "Debug", is not a
    # substring of the echoed "keywords RobotDebug" command.
    Should Contain    ${out}    Variables

List Keywords Short Alias K
    [Tags]    libdoc
    ${input}=    Lines
    ...    k\tBuiltIn
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Keywords of library BuiltIn
    Should Contain    ${out}    Log To Console

Show Keyword Documentation
    [Tags]    libdoc
    ${input}=    Lines
    ...    docs\tDebug
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    interactive shell

Show Keyword Documentation Short Alias D
    [Tags]    libdoc
    ${input}=    Lines
    ...    d\tLog To Console
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Logs the given message to the console.

List Available Output Styles
    ${input}=    Lines    style    exit
    ${out}=    Run Interactive Shell    ${input}
    # "monokai" is a Pygments style available in every supported version.
    Should Contain    ${out}    monokai

Set Output Style
    ${input}=    Lines
    ...    style\tmonokai
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Set style to:
    Should Contain    ${out}    monokai

Unknown Style Does Not Crash The Shell
    # Regression for C2: a style name with no fuzzy match used to raise
    # IndexError and kill the whole session.
    ${input}=    Lines
    ...    style\tzzzznotastyle
    ...    Log To Console\tSHELL_SURVIVED_BAD_STYLE
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    unknown style
    Should Contain    ${out}    SHELL_SURVIVED_BAD_STYLE

Clear Screen Does Not Crash The Shell
    # clear/cls emits terminal escapes; assert a later keyword still runs.
    ${input}=    Lines
    ...    cls
    ...    Log To Console\tALIVE_AFTER_CLEAR
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    ALIVE_AFTER_CLEAR

Help Without Arguments
    ${input}=    Lines    help    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Input Robotframework keywords

Help For A Specific Command
    ${input}=    Lines    help libs    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Print imported

Help For A Command Alias
    ${input}=    Lines    help c    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Continue execution.

Question Mark Is A Help Prefix
    [Tags]    libdoc
    ${input}=    Lines
    ...    ?keywords
    ...    exit
    ${out}=    Run Interactive Shell    ${input}
    Should Contain    ${out}    Print keywords of libraries
