# Device Test Runner v1.5.3 Test Matrix

Release theme: Selective Retry and Artifact Criticality

| Requirement | Scenario | Level | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| Selective retry parsing | Valid failure types configured | Unit | Values become ordered `FailureType` entries | `tests/test_unit/test_config_loader.py` |
| Retry default | YAML omits `retry_on` | Unit | Retry list is empty | `tests/test_unit/test_config_loader.py` |
| Retry validation | Unknown type or `none` configured | Unit | Configuration raises `ValueError` | `tests/test_unit/test_config_loader.py` |
| Retry normalization | Duplicate failure types configured | Unit | Duplicates are removed | `tests/test_unit/test_config_loader.py` |
| Policy allow-list | Configured failure occurs before limit | Unit | Retry is allowed | `tests/test_unit/test_retry.py` |
| Policy rejection | Unconfigured failure occurs | Unit | Retry is denied | `tests/test_unit/test_retry.py`, `tests/test_unit/test_runner.py` |
| Required default | Rule omits `required` | Unit | Rule is required | `tests/test_unit/test_config_loader.py` |
| Optional artifact | Optional validation fails | Unit | Result is reported; step and run pass | `tests/test_unit/test_runner.py` |
| Required artifact | Required validation fails | Unit | Step or final run fails | `tests/test_unit/test_runner.py` |
| Required retry | Required artifact fails with matching `retry_on` | Unit + Integration | Target is cleaned and step retries | `tests/test_unit/test_runner.py`, `tests/test_integration/test_integration_retry.py` |
| Cleanup boundary | Target is optional, missing, or outside run directory | Unit | Target is retained or safely ignored | `tests/test_unit/test_cleanup.py` |
| Summary accounting | Optional and required failures coexist | Unit | All failures and required failures are counted separately | `tests/test_unit/test_runner.py`, `tests/test_unit/test_reporter.py` |
| Version reporting | Run completes | Integration | `runner_version` is `1.5.3` | `tests/test_integration/test_integration.py`, `tests/test_integration/test_integration_artifact_validation.py` |
| Regression | Existing lifecycle, validation and classification paths run | Unit + Integration | Existing contracts remain green | `tests/test_unit/`, `tests/test_integration/` |

## Verification Baseline

* Command: `poetry run pytest -q`
* Result: **134 passed in 25.45s** (verified 2026-09-04)
