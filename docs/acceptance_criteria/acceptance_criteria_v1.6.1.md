# Device Test Runner v1.6.1 Acceptance Criteria

## Scope

Safe Process Termination on POSIX. Runtime is `1.6.1`; distribution version synchronization and release verification remain pending.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | a direct process already exited | termination is requested | no group signal is sent; its return code is preserved. |
| AC-2 | a live attempt group accepts SIGTERM | cleanup starts | the group exits during the grace period without SIGKILL. |
| AC-3 | a process or its descendants ignore SIGTERM | the grace period expires | SIGKILL stops the remaining group members. |
| AC-4 | parent, child and grandchild share the attempt group | timeout or cancellation is observed | the three PIDs disappear; timeout and cancellation remain distinct. |
| AC-5 | the processes have written stdout and stderr | executor cleanup completes | both reader threads stop and result output matches the saved log files. |
| AC-6 | a first attempt times out with a child process | the second attempt starts | it immediately confirms both previous PIDs are absent before succeeding. |
| AC-7 | a token is cancelled with retries available | runner handles cancellation | no cancelled retry occurs; reachable teardown/global_teardown use active execution tokens. |
| AC-8 | the SIGINT handler has an active token | it receives its first invocation | it cancels the token without raising KeyboardInterrupt. |
| AC-9 | the handler already received one invocation | it is invoked again | it raises KeyboardInterrupt and the token stays cancelled. |

## Verification and decision

- [x] AC-1 through AC-9 map to the [Test Matrix](../test_matrix/test_matrix_v1.6.1.md).
- [x] Local test results and test-docstring checks are recorded in [Definition of Done](../definition_of_done/definition_of_done_v1.6.1.md).
- [x] Architecture includes process-group and retry sequence diagrams.
- [ ] Distribution and runtime versions are synchronized.
- [ ] Real CLI SIGINT delivery, exit codes and handler restoration are verified end to end.
- [ ] Ubuntu CI results and GitHub issue/milestone state are verified.
- [ ] v1.6.1 tag and GitHub Release publication are verified.

The tested process-group behavior is accepted within the documented scope. Full release readiness is not established. AC-7 uses runner mocks; AC-8/9 directly invoke the handler. Neither proves finalization after a second real Ctrl+C.
