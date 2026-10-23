# Device Test Runner v1.7.1 Test Matrix

Scope: host environment references and early device.serial resolution. Source baseline `c1d457c`; implementation history `f98ca30` through HEAD. [Execution record](../definition_of_done/definition_of_done_v1.7.1.md); [pytest techniques](../test_guide.md#v1-7-1).

## Requirement coverage

| Requirement | Test path / function | Assertions and boundary |
| --- | --- | --- |
| Resolve serial without mutation | `tests/test_unit/test_env_variables.py::test_env_device_serial` | Resolved serial and unchanged original DeviceInfo |
| Mixed env/vars command and run.dir path | `tests/test_unit/test_env_variables.py::test_env_command_and_path` | Exact command string and absolute path; path assertion itself uses run.dir, not env |
| Missing name | `tests/test_unit/test_env_variables.py::test_missing_env_is_fail_fast` | VariableResolutionError and message |
| Invalid syntax | `tests/test_unit/test_env_variables.py::test_invalid_env_expression` | Three parameterized expressions raise |
| Empty is defined | `tests/test_unit/test_env_variables.py::test_empty_environment_variable_is_defined` | Explicit environ mapping returns empty string |
| Snapshot | `tests/test_unit/test_env_variables.py::test_environment_is_snapshpt` | Host change after resolver construction does not alter lookup; existing function spelling retained |
| No implicit timeout conversion | `tests/test_unit/test_env_variables.py::test_env_does_not_change_numeric_timeout` | String 600 rejected by timeout() |
| YAML → real subprocess → report | `tests/test_integration/test_integration_static_variables.py::test_environment_serial_from_yaml_to_report` | Unresolved loaded config; PASSED RunResult; resolved serial in metadata and parsed result.json |
| Early failure before run allocation | `tests/test_integration/test_integration_static_variables.py::test_missing_env_prevents_run_directory_creation` | Missing serial env raises; existing output parent has no entries; no direct executor/watchdog spy |
| Static substitution regression | `tests/test_unit/test_variables.py`, `tests/test_integration/test_integration_static_variables.py` | Typed vars, eager field failures, CSV/report and separate runs; see historical v1.7.0 matrix |
| Report version | `tests/test_unit/test_runner.py::test_cancellation_lifecycle_and_summary`, `tests/test_integration/test_integration.py::test_yaml_to_result_json`, `tests/test_integration/test_integration_artifact_validation.py::test_csv_and_json_content_validation` | Explicit runner_version 1.7.1 assertions |

## Fix history and collaboration

Git history documents the following fixes; commit authorship is not inferred as AI work. This documentation session adds Given/When/Then descriptions to nine tests, without changing executable statements.

| Original failure | Fix / history | Regression evidence |
| --- | --- | --- |
| Environment snapshot used dict subscription syntax and lacked os import | `88a50f4`, `e6f1ad3`: construct dict and import os | Snapshot and env serial unit tests |
| Runner referenced run_dir before assignment and misspelled its later update; DeviceInfo used repalce | `574d0f6`: initial Path.cwd(), actual run_dir, replace() | Real YAML-to-report and missing-env integration cases |
| Lookup used an undefined environ variable | `1ad70cb`: read self.environ | Env command, serial and explicit mapping cases |
| Tests had decorator, fixture, expectation and report-loading errors | Subsequent test-fix commits through `3dae08f`; inspect final tests for actual assertions | Collection and full-suite result, rather than a claim of production behavior changes |

## Gaps and boundaries

Env interpolation in validation paths, env values containing template markers, cross-run environment changes, and host changes during actual attempts lack dedicated integration tests. Source inspection establishes serial resolution ordering and separate live subprocess environments. No run/step mapping, default values or secret masking exists. The legacy test_unknown_or_malformed_expression_fails includes env.SECRET and depends on that host variable being absent. No dedicated hardware, Linux CI, concurrent mutation or external release result was observed in this task.
