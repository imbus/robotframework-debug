*** Settings ***
Documentation       Step debugging driven by the function keys RobotDebug binds:
...                 F7 INTO, F8 OVER, F9 OUT, F10 CONTINUE and Shift-Tab DETACH.
...                 The shell is entered through the ``Debug`` keyword and the
...                 keys are sent as their raw terminal escape sequences (the
...                 ``<F8>`` placeholders are expanded by the helper library).

Resource            ../resources/shell.resource

Force Tags          step


*** Test Cases ***
Step Over Executes Each Line And Stops At The Next
    # F8 (OVER) four times walks the three statements after Debug, then F10.
    ${out}=    Run Task In Debug Mode    step_task.robot    <F8><F8><F8><F8><F10>
    Should Contain    ${out}    step_task.robot:9
    Should Contain    ${out}    step-line-1
    Should Contain    ${out}    step_task.robot:11
    Should Contain    ${out}    step-line-2

Step Over Runs A User Keyword In One Step
    # Outer Keyword (which calls Inner Keyword) runs fully on a single F8.
    ${out}=    Run Task In Debug Mode    step_task.robot    <F8><F8><F8><F10>
    Should Contain    ${out}    outer-start
    Should Contain    ${out}    inner-line
    Should Contain    ${out}    outer-end

Step Into Descends Into A User Keyword
    # F8,F8 to reach "Outer Keyword", then F7 (INTO) to enter the resource file.
    ${out}=    Run Task In Debug Mode    step_task.robot    <F8><F8><F7><F8><F8><F8><F10>
    Should Contain    ${out}    keywords.resource:
    Should Contain    ${out}    outer-start
    Should Contain    ${out}    inner-line

Continue Runs The Rest Without Stopping
    ${out}=    Run Task In Debug Mode    step_task.robot    <F10>
    Should Contain    ${out}    step-line-1
    Should Contain    ${out}    step-line-2

Detach Runs The Rest Without Opening The Shell Again
    # Shift-Tab detaches: the remaining keywords execute but no further stop.
    ${out}=    Run Task In Debug Mode    step_task.robot    <STAB>
    Should Contain    ${out}    step-line-1
    Should Contain    ${out}    step-line-2
    Should Not Contain    ${out}    step_task.robot:11
