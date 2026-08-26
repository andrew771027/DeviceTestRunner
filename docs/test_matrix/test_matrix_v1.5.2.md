# Device Test Runner v1.5.2 Test Matrix

Release theme: Failure Classification

| Requirement | Scenario | Level | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| Successful classification | Process succeeds | Unit | Failure type is `NONE` | `tests/test_unit/test_failure.py` |
| Timeout classification | Process exceeds step timeout | Unit + Integration | Attempt fails as `TIMEOUT`; partial logs remain available | `tests/test_unit/test_executor.py`, `tests/test_integration/test_integration_failure.py` |
| Device connectivity | stderr reports offline, missing, or unauthorized device | Unit + Integration | Attempt fails as `DEVICE_OFFLINE` | `tests/test_unit/test_failure.py`, `tests/test_integration/test_integration_failure.py` |
| Process classification | Command returns non-zero without device pattern | Unit + Integration | Attempt fails as `PROCESS_ERROR`; exit code is preserved | `tests/test_unit/test_executor.py`, `tests/test_integration/test_integration_failure.py` |
| Missing artifact | Required path does not exist | Unit | Validation and attempt use `ARTIFACT_MISSING` | `tests/test_unit/test_artifact_validator.py`, `tests/test_unit/test_runner.py` |
| Invalid artifact | Artifact exists but violates size, extension, CSV, JSON, or directory contract | Unit | Validation and attempt use `ARTIFACT_INVALID` | `tests/test_unit/test_artifact_validator.py`, `tests/test_unit/test_runner.py` |
| Artifact priority | Missing and invalid artifact results coexist | Unit | Aggregate classification is `ARTIFACT_MISSING` | `tests/test_unit/test_failure.py` |
| Process priority | Process and artifact failure could coexist | Unit | Process failure remains the attempt root category | `tests/test_unit/test_runner.py` |
| Retry eligibility | Retryable failure occurs before max attempts | Unit | Policy permits another attempt | `tests/test_unit/test_retry.py` |
| Retry success | Later attempt succeeds | Unit + Integration | Final step passes; attempt history retains prior failure | `tests/test_unit/test_runner.py`, `tests/test_integration/test_integration_retry.py` |
| Retry exhaustion | Failure continues through max attempts | Unit + Integration | Policy stops; step and run fail | `tests/test_unit/test_retry.py`, `tests/test_integration/test_integration.py` |
| Attempt reporting | Attempt is serialized | Unit + Integration | `failure_type`, logs, exit code, timing, and validation results are available | `tests/test_unit/test_reporter.py`, `tests/test_integration/test_integration.py` |
| Final validation | Non-retry-enabled artifact rule fails | Unit + Integration | Final run status is `FAILED` without step retry | `tests/test_unit/test_runner.py`, `tests/test_integration/test_integration_artifact_validation.py` |
| Lifecycle guarantees | Setup or scenario step fails | Unit + Integration | Later scenario work is skipped while required teardown stages run | `tests/test_unit/test_runner.py`, `tests/test_integration/test_integration.py` |

## Verification Baseline

- Test functions collected: 112
- Full command: `poetry run pytest -q`
- Result: 112 passed
- BDD description audit: 112 of 112 tests contain Given／When／Then
