*** Settings ***
Library     RobotDebug
Resource    keywords.resource


*** Tasks ***
Debug Keyword Task
    ${secret} =    Set Variable    pre-debug-value
    Debug
    Log To Console    post-debug-line
