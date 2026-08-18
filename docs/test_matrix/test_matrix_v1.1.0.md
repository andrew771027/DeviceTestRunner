# Device Test Runner v1.1.0 Test Matrix

Baseline: Git tag `v1.1.0`

| Area | Test level | Expected result | Historical evidence |
| --- | --- | --- | --- |
| YAML contract | Unit | Renamed YAML fields remain valid | `tests/test_contract_config_yaml.py` |
| Runner config loading | Unit | YAML maps to the renamed runner models | `tests/test_runner_loader.py` |
| Command executor naming | Unit | Command execution uses the v1.1 model names without pytest collection conflicts | `tests/test_command_executor.py` |
| Runner aggregation | Unit | Step results use the updated model contract | `tests/test_runner.py` |
| End-to-end compatibility | Integration | The renamed model pipeline still executes a sample configuration | `tests/test_integration.py` |

Regression focus: v1.0 behavior remains intact after naming and model refactoring.
