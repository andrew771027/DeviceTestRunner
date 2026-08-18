# Device Test Runner v1.5.0 Test Matrix

Baseline: Git tag `v1.5.0`

| Area | Test level | Expected result | Historical evidence |
| --- | --- | --- | --- |
| Retry defaults | Unit | Missing retry config executes once with zero delay | `tests/test_config_loader.py` |
| Retry validation | Unit | Attempts below one or negative delay are rejected | `tests/test_config_loader.py` |
| Retry policy | Unit | Failures retry before the limit; success and exhausted attempts stop | `tests/test_retry.py` |
| Attempt aggregation | Unit | `StepResult` records every attempt and final success | `tests/test_runner.py` |
| Retry delay | Unit | Configured delay is applied only between attempts | `tests/test_runner.py` |
| Per-attempt logs | Unit | Each attempt gets independent stdout/stderr files | `tests/test_runner.py` |
| Real subprocess retry | Integration | A transient command can pass on a later attempt; exhaustion fails | `tests/test_integration.py` |

Out of scope: artifact validation as an attempt-level retry trigger.
