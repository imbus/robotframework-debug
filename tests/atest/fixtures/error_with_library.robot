*** Settings ***
Library     RobotDebug
Resource    keywords.resource


*** Tasks ***
Failing Task With Library Imported
    Log To Console    before-failure-lib
    Should Be Equal    1    2    boom-with-library
