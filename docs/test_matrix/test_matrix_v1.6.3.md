# Device Test Runner v1.6.3 Test Matrix

Version scope: Cancellation-Aware Cleanup. Evidence: `f9337ec` plus the inspected working tree, compared with `v1.6.2`. Real subprocess tests also live in the unit directory. Writing techniques are in the [v1.6.3 test guide](../test_guide.md#v1-6-3).

## Requirement coverage

Paths below are under `tests/test_unit/` unless stated otherwise.

| Requirement | Test | Evidence and boundary |
| --- | --- | --- |
| Invalid cleanup budget rejected | `test_config_loader.py::test_invalid_cleanup_timeout_is_rejected` | Eight parser inputs: zero, negatives, booleans, NaN and infinities; calls parser directly, not full YAML load |
| Missing budget unlimited | `test_config_loader.py::test_missing_cleanup_timeout_is_unlimited` | Parser returns None; null/positive cleanup values and full YAML routing lack dedicated assertions |
| Cleanup watchdog reason | `test_watchdog.py::test_cleanup_watchdog_uses_cleanup_timeout_reason` | Real thread, bounded monotonic polling, CLEANUP_TIMEOUT |
| Independent cleanup token | `test_runner.py::test_teardown_uses_independent_cancellation_scope` | Mock records scenario token and shared distinct teardown/global teardown token |
| Cancel before run | `test_runner.py::test_cancel_before_run_only_runs_global_teardown` | Only global_teardown executes |
| Global setup fails | `test_runner.py::test_global_setup_failure_only_run_global_teardown` | Skips setup/scenario/teardown; global_teardown executes |
| Cleanup budget interrupts attempt | `test_runner.py::test_cleanup_timeout_cancels_teardown` | Real subprocess: CANCELLED attempt, cleanup_timeout summary, run FAILED |
| Preserve run reason | `test_runner.py::test_cleanup_timeout_does_not_override_run_timeout` | Both deadlines recorded, final TIMED_OUT; scenario command has unmatched quote, so this is not clean evidence of interrupting a sleeping scenario |
| Step timeout distinct | `test_runner.py::test_teardown_step_timeout_is_not_cleanup_timeout` | TIMEOUT attempt, timed_out=true; cleanup failed but scope did not time out |
| Validate partial CSV | `test_runner.py::test_cancelled_run_still_validates_partial_artifacts` | Real scenario writes one row where two required; one cancelled attempt, ARTIFACT_INVALID, TIMED_OUT, successful cleanup |
| Missing artifact preserves cancellation | `test_runner.py::test_missing_artifact_does_not_override_cancellation` | Pre-cancelled user token; ARTIFACT_MISSING with CANCELLED |
| Stop remaining cleanup | `test_runner.py::test_cleanup_timeout_stops_remaining_cleanup_steps` | Cleanup timeout and absent marker; `touch -c` does not create an absent marker even if executed, so non-execution needs stronger evidence |
| JSON cleanup summary | `test_reporter.py::test_save_result_json` | Serialized cleanup_summary equals dataclass asdict |
| Status rules | `test_run_status.py::test_run_status_matrix` | Parameterized counts/status; cleanup_failed passed as false, so direct cleanup priority combinations remain incomplete |
| Existing integration regression | `tests/test_integration/test_integration_runner_timeout.py` | Existing timeout/cleanup marker paths run as part of full suite |

## AI collaboration and fixes

This chat provides attribution for the following work; no authorship is inferred for other cases.

| Case | Original gap | Change and regression evidence | Remaining limit |
| --- | --- | --- | --- |
| Cancel before run | global_teardown nested under successful setup condition caused empty executed_steps | Moved global_teardown outside that condition; existing cancel-before-run and global-setup-failure tests exercise the path | Exception finalization remains open |
| Cleanup timeout attempt | `bash 'sleep 60s'` treated text as a script filename, reporting PROCESS_ERROR before retry-delay cancellation | Corrected fixture to `bash -c 'sleep 60'`; cleanup timeout test asserts CANCELLED attempt | Thread scheduling is real time |
| Partial CSV | User requested complete runnable test without missing helpers | Provided explicit config, real runner and one-row CSV with min_rows=2; adopted test asserts cancellation and final invalid artifact | Missing artifact is a separate test; no guaranteed validation wall-clock budget |
| Test descriptions | Ten functions lacked concrete Given/When/Then descriptions | Added docstrings only; executable AST checked separately | Descriptions do not strengthen weak marker/command evidence |

## Verification

pytest.ini uses `testpaths = tests`. On 2026-10-07, `.venv/bin/python -m pytest --collect-only -q` collected 223 cases in 0.17s without warnings. The full suite then passed: `.venv/bin/python -m pytest -q` — 223 passed in 47.37s, without warnings. Earlier missing-testpaths warnings came from the INI configuration, not an individual test.

Observed commands, environment and current results are recorded in [Definition of Done](../definition_of_done/definition_of_done_v1.6.3.md). Passing local tests do not prove Linux CI, release publication, boundary races, shared deadline accumulation across multiple successful cleanup steps, cleanup retry delay interruption, or exception-safe reports.
