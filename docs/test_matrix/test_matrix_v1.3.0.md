# Device Test Runner v1.3.0 Test Matrix

Baseline: Git tag `v1.3.0`

| Area | Test level | Expected result | Historical evidence |
| --- | --- | --- | --- |
| Lifecycle success | Unit | `global_setup`, `setup`, `scenario`, `teardown`, and `global_teardown` execute in order | `tests/test_runner.py` |
| Scenario failure | Unit | Later scenario steps stop while teardown paths still run | `tests/test_runner.py` |
| Setup failure | Unit | Scenario and teardown are skipped; global teardown is preserved | `tests/test_runner.py` |
| Artifact layout | Unit | Stage and step output paths are generated consistently | `tests/test_artifact.py` |
| Result reporting | Unit | Lifecycle results serialize into `result.json` | `tests/test_reporter.py` |
| Lifecycle execution | Integration | YAML executes across the complete lifecycle | `tests/test_integration.py` |

Regression focus: v1.2 artifact and executor behavior remains compatible with lifecycle orchestration.
