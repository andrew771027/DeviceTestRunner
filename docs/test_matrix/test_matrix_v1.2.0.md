# Device Test Runner v1.2.0 Test Matrix

Baseline: Git tag `v1.2.0`

| Area | Test level | Expected result | Historical evidence |
| --- | --- | --- | --- |
| Artifact directory | Unit | A unique run directory is created for a test case | `tests/test_runner.py` |
| stdout/stderr persistence | Unit | Command output is written under the run artifacts | `tests/test_executor.py` |
| Artifact models | Unit | Artifact paths and run metadata serialize correctly | `tests/test_models.py` |
| Config loading | Unit | Existing YAML remains loadable after ArtifactManager integration | `tests/test_config_loader.py` |
| JSON report | Integration | A run produces persisted output and report data | `tests/test_integration.py` |

Out of scope: lifecycle failure routing, streaming console output, artifact validation, and retry.
