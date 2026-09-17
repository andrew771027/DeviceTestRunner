# Device Test Runner v1.4.1 Test Matrix

Version baseline: Git tag `v1.4.1`

| Area | Test level | Expected result | Historical evidence |
| --- | --- | --- | --- |
| CSV schema | Unit | Required columns and minimum rows are validated | `tests/test_artifact_validator.py` |
| CSV error handling | Unit | Missing, invalid, non-UTF-8, or directory paths fail clearly | `tests/test_artifact_validator.py` |
| JSON paths | Unit | Required nested JSON paths are resolved | `tests/test_artifact_validator.py` |
| JSON expected values | Unit | Values and value types must match | `tests/test_artifact_validator.py` |
| Config mapping | Unit | CSV and JSON options load from YAML | `tests/test_config_loader.py` |
| Content validation | Integration | Valid content passes; invalid CSV/JSON makes the run fail | `tests/test_integration_artifact_validation.py` |

Regression focus: all v1.4.0 file and directory rules remain supported.

## Pytest 用法

Fixture、mock、參數化與執行方式請見 [測試指南 v1.4.1](../test_guide.md#v1-4-1)。
