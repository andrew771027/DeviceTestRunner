# Device Test Runner v1.6.0 Test Matrix

Version scope: Cancellation Foundation

| Requirement | Scenario | Level | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| Token state | Initial state, repeated cancel, exception helper | Unit | Active initially; cancellation persists; helper raises only after cancel | `test_cancellation.py`: all five tests |
| Configuration | `retry_on` includes `cancelled` | Unit | `ValueError` | `test_config_loader.py::test_retry_on_cancelled_is_invalid` |
| Retry prohibition | Python config includes CANCELLED with attempts remaining | Unit | Policy still denies retry | `test_retry.py::test_cancelled_is_never_retried` |
| Real cancellation | Thread cancels a running shell command | Integration | CANCELLED, not TIMEOUT; started stdout preserved | `test_integration_cancellation.py::test_executor_cancels_running_process` |
| Timeout distinction | Real command exceeds timeout | Integration | TIMEOUT, timed_out true, cancelled false | `test_integration_failure.py::test_executor_classifies_timeout` |
| Executor regression | Success, failure, completed-process polling, timeout | Unit | Existing logs, environment and result fields preserved | `test_executor.py` |
| Lifecycle routes | Cancel before run, in global_setup, setup or scenario | Unit, four parameter cases | Reachable cleanup executes with active tokens; correct skipped/cancelled counts and JSON | `test_runner.py::test_cancellation_lifecycle_and_summary` |
| Scenario cancellation | Cancel first of several scenario steps | Unit | Remaining scenario skipped; both cleanup stages run | `test_runner.py::test_cancel_stops_remaining_scenario_steps` |
| No cancelled retry | Cancel scenario with attempts available | Unit | One cancelled attempt only | `test_runner.py::test_cancelled_step_is_not_retried` |
| Pre-cancelled run | Token cancelled before run | Unit | Only global_teardown executes | `test_runner.py::test_cancel_before_run_only_runs_global_teardown` |
| Retry delay polling | Cancel during first fake-clock sleep | Unit | Delay returns after 0.1 simulated seconds | `test_runner.py::test_cancel_during_retry_delay` |
| Retry delay routing | Cancel after failed global_setup attempt | Unit | No second attempt; global_teardown still runs | `test_runner.py::test_cancel_during_retry_delay_stops_next_attempt_and_runs_cleanup` |
| Artifact cancellation | Cancel with a required missing bound artifact | Unit | Skip attempt validation, retain final validation, status remains CANCELLED | `test_runner.py::test_cancelled_attempt_skips_validation_and_preserves_cancellation` |
| Serialization | Metadata, summary, attempts and validation results | Unit + Integration | JSON preserves cancellation fields and runtime 1.6.0 | `test_reporter.py::test_save_result_json`, lifecycle parameter cases, `test_integration.py` |
| Regression | Selective retry, optional artifacts, cleanup, CSV/JSON validation | Unit + Integration | Existing contracts pass | `tests/test_unit/`, `tests/test_integration/` |

Unit filenames above resolve under `tests/test_unit/`; integration filenames resolve under `tests/test_integration/`.

## Verification baseline

Verification date: 2026-09-12. Comparison baseline: Git tag `v1.5.3`. Verification covers the current v1.6.0 source and test changes; target tag `v1.6.0` has not yet been created.

Verification on 2026-09-12 (local Python 3.14): `.venv/bin/python -m pytest -q` → **153 passed in 39.39s**. This is local evidence, not a successful GitHub Actions Python 3.12 run. `git diff --check` passed; local Markdown links and JSON examples validated.

All 150 Python test functions under `tests/` were audited for meaningful Given／When／Then docstrings. Of these, 121 descriptions were added or corrected; 29 existing descriptions were retained. An AST comparison against HEAD with function docstrings removed confirmed unchanged executable test code. Parametrization of the lifecycle cancellation test adds three cases beyond the function count.

## Coverage limits

* Real cancellation integration calls the executor; lifecycle cancellation routing uses mocks. This does not prove a complete real-process runner cancellation sequence.
* The integration test checks preserved output and classification, not a maximum shutdown duration or absence of surviving descendants.
* Force-kill fallback, signal handling, unhandled-exception cleanup and the post-global_setup cancellation boundary are not established by dedicated tests.
* `test_retry_policy_retries_failure_before_max_attempts` actually supplies `FailureType.NONE` and asserts false for attempts one and two. Its docstring now describes those assertions; it is not evidence for failure retry. Other policy and runner tests cover actual failure retry.
* `test_artifact_retry_defaults_to_false` checks an explicit optional rule and absent `after_step`, not a removed `retry_on_failure` default.
* `configs/sample.yaml` is a demonstration configuration, not a proven all-pass acceptance run; see Definition of Done for the observed sample result.
