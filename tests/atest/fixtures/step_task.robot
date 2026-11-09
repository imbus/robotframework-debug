*** Settings ***
Library     RobotDebug
Resource    keywords.resource


*** Tasks ***
Step Task
    Debug
    Log To Console    step-line-1
    Outer Keyword
    Log To Console    step-line-2
