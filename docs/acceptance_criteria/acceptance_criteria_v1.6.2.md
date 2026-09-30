# Device Test Runner v1.6.2 Acceptance Criteria

Version scope: Run-level Timeout. These criteria describe the inspected working tree, not release approval.

| ID | Given | When | Then | Evidence / status |
| --- | --- | --- | --- | --- |
| AC-1 | YAML omits run timeout | Configuration loads | Timeout is None; step timeout remains available | Verified by configuration test and source |
| AC-2 | Zero, negative, non-finite or boolean timeout | Parser validates | ValueError rejects the value | Verified, parameterized tests |
| AC-3 | A token already has a reason | Another cancellation arrives | First reason is preserved | Verified in both orders |
| AC-4 | A running watchdog | Deadline expires or stop joins it | Deadline requests RUN_TIMEOUT; stopped thread does not remain running | Verified, watchdog tests |
| AC-5 | A long command with a longer step timeout | Run deadline expires | Command is cancelled, no retry, remaining scenario steps do not run | Verified, real subprocess |
| AC-6 | A failed attempt waiting to retry | Run deadline expires | No new attempt; original PROCESS_ERROR remains | Verified, JSON assertions |
| AC-7 | Setup is interrupted after global setup succeeded | Cleanup begins | Teardown and global_teardown execute; scenario is skipped | Verified, file markers |
| AC-8 | Run timeout cancellation | Result is built and saved | TIMED_OUT with run_timeout reason; attempt flags preserve step/run distinction | Verified, status and integration tests |
| AC-9 | A step reaches its own timeout | Executor returns | FailureType.TIMEOUT and timed_out=true | Verified, mocked executor timing |
| AC-10 | Direct child is reaped but its group survives | Terminator is invoked | Descendant exits and terminated=true | Verified, real orphan fixture |

Tests and boundaries are mapped in the [test matrix](../test_matrix/test_matrix_v1.6.2.md). Exact local results are in the [Definition of Done](../definition_of_done/definition_of_done_v1.6.2.md).

## Acceptance limits

Run timeout is not a hard upper bound on cleanup, artifact validation or report writing. CLI currently returns 0 for TIMED_OUT; nonzero CLI timeout handling is not accepted as complete. Unexpected-exception finalization, Linux CI, detached descendants, version synchronization and publication remain open. Local tests do not establish release readiness for these boundaries.
