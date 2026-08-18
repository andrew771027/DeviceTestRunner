# Device Test Runner v1.4.0 Test Matrix

Baseline: Git tag `v1.4.0`

| Area | Test level | Expected result | Historical evidence |
| --- | --- | --- | --- |
| File existence | Unit | Existing files pass and missing files fail | `tests/test_artifact_validator.py` |
| File size | Unit | Minimum/maximum constraints affect validation results | `tests/test_artifact_validator.py` |
| File extension | Unit | Allowed extensions pass and disallowed extensions fail | `tests/test_artifact_validator.py` |
| Directory contents | Unit | Non-empty directory validation distinguishes empty or invalid paths | `tests/test_artifact_validator.py` |
| Validation aggregation | Unit | All configured rules return results and affect run status | `tests/test_runner.py` |
| Validation report | Integration | Validation results are persisted in `result.json` | `tests/test_integration_artifact_validation.py` |

Out of scope: CSV/JSON semantic validation and retry.
