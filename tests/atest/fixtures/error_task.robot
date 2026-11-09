*** Settings ***
Resource    keywords.resource


*** Variables ***
${UNREACHED_MARKER}     SENTINEL_THAT_RAN


*** Tasks ***
Failing Task
    Log To Console    before-failure
    Should Be Equal    1    2    boom-intentional-failure
    Log To Console    ${UNREACHED_MARKER}
