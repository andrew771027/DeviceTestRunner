# Device Test Runner v1.0.0 Test Matrix

Baseline: Git tag `v1.0.0`

| Area | Test level | Expected result | Historical evidence |
| --- | --- | --- | --- |
| YAML contract | Unit | Required top-level sections and step fields can be represented | `tests/test_contract_config_yaml.py` |
| Configuration loading | Unit | YAML is converted into runner models | `tests/test_config_loader.py` |
| Command execution | Unit | A subprocess success or failure is returned to the runner | `tests/test_subprocess_executor.py` |
| Basic orchestration | Unit | Configured steps execute and produce step results | `tests/test_runner.py` |
| End-to-end execution | Integration | Sample YAML runs through executor and produces JSON output | `tests/test_integration.py` |

Out of scope: artifact directories, full lifecycle stages, validation, retry, and timeout cancellation.
