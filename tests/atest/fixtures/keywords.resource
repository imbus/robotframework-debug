*** Keywords ***
Greet
    [Arguments]    ${name}
    Log To Console    hello-${name}
    RETURN    greeting-for-${name}

Outer Keyword
    Log To Console    outer-start
    Inner Keyword
    Log To Console    outer-end

Inner Keyword
    Log To Console    inner-line
