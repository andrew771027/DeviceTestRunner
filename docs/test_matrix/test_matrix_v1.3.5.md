# Device Test Runner v1.3.5 Test Matrix

Baseline: Git tag `v1.3.5`

| Area | Test level | Expected result | Historical evidence |
| --- | --- | --- | --- |
| stdout streaming | Unit | stdout is shown on the console and persisted | `tests/test_console_output.py`, `tests/test_executor.py` |
| stderr streaming | Unit | stderr is shown on the console and persisted | `tests/test_console_output.py`, `tests/test_executor.py` |
| Immediate writes | Unit | Log output is flushed without waiting for process completion | `tests/test_artifact.py` |
| Failure diagnostics | Unit | Failed steps retain stdout, stderr, exit code, and log paths | `tests/test_runner.py` |
| End-to-end log pipeline | Integration | Console/executor/artifact output remains synchronized | `tests/test_integration.py` |

Regression focus: lifecycle routing from v1.3.0 remains unchanged.
