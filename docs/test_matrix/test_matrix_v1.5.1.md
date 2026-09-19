# Device Test Runner v1.5.1 Test Matrix

Historical baseline: the working tree after tag `v1.5.0` (release candidate; no `v1.5.1` tag yet)

| Area | Test level | Expected result | Recorded evidence |
| --- | --- | --- | --- |
| Rule loading | Unit | `after_step` loads and `retry_on_failure` defaults to false | `tests/test_unit/test_config_loader.py` |
| Rule filtering | Unit | Only opted-in rules associated with the current step run per attempt | `tests/test_unit/test_runner.py` |
| Artifact recovery | Unit | Command pass + artifact fail retries and can later pass | `tests/test_unit/test_runner.py` |
| Artifact exhaustion | Unit | Repeated artifact failure exhausts attempts and fails the step | `tests/test_unit/test_runner.py` |
| Non-retryable validation | Unit | A rule without opt-in does not retry, but final validation can fail the run | `tests/test_unit/test_runner.py` |
| Attempt report | Unit | Each `StepAttemptResult` contains its artifact validation results | `tests/test_unit/test_runner.py`, `tests/test_unit/test_models.py` |
| Stale artifact cleanup | Unit | Retry targets are removed before a new attempt | `tests/test_unit/test_cleanup.py` — currently failing/not integrated |
| Real artifact-aware retry | Integration | Invalid first artifact retries and valid second artifact passes | `tests/test_integration/test_integration_retry.py` — currently blocked by invalid YAML fixture |

Targeted test result recorded for this candidate: 24 passed, 2 failed. The two failures above must be resolved before release acceptance.

## Pytest 用法

Fixture、mock、參數化與執行方式請見 [測試指南 v1.5.1](../test_guide.md#v1-5-1)。
