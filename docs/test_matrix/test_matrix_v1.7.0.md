# Device Test Runner v1.7.0 Test Matrix

Version scope: Static Variable Substitution. Baseline: `194faf3` plus the inspected working tree. Results are recorded in [Definition of Done](../definition_of_done/definition_of_done_v1.7.0.md); writing techniques are in the [v1.7.0 test guide](../test_guide.md#v1-7-0).

## Requirement coverage

| Requirement | Test path / function | Evidence and boundary |
| --- | --- | --- |
| Command interpolation and repeated references | `tests/test_unit/test_variables.py::test_command_interpolation`, `test_multiple_references` | Checks rendered strings; does not execute them |
| Integer type preservation | `tests/test_unit/test_variables.py::test_timeout_preserves_integer` | Whole reference returns exact int type |
| Positive int/float timeout | `tests/test_unit/test_variables.py::test_timeout_accepts_positive_numbers` | Three values, both direct and referenced, exact value/type |
| Absolute artifact path | `tests/test_unit/test_variables.py::test_artifact_path`, `test_resolve_artifact_rules` | Checks run.dir and filename interpolation |
| Undefined / malformed / unsupported expression | `tests/test_unit/test_variables.py::test_unknown_or_malformed_expression_fails` | Missing name, env namespace, arithmetic and incomplete braces |
| Invalid definitions / recursion | `tests/test_unit/test_variables.py::test_invalid_variable_definitions`, `test_unsupported_nested_tempalte` | List, mapping, invalid name, nested vars and run.dir references; function spelling retained |
| Invalid timeout rejected | `tests/test_unit/test_variables.py::test_invalid_timeout_values` | Twelve values covering string, bool, zero, negative, NaN, infinity and null |
| Command type requirement | `tests/test_unit/test_variables.py::test_missing_value_fails_as_string` | Whole integer reference cannot become a command; no separate whole numeric path test |
| Immutable configuration | `tests/test_unit/test_variables.py::test_resolve_models_without_mutating_original` | Resolved command/timeout and unchanged original command; uses test-local dataclasses |
| YAML → subprocess → CSV → report | `tests/test_integration/test_integration_static_variables.py::test_yaml_to_subprocess_artifact_and_json_report` | Real Python subprocess, four CSV lines, resolved command/path, PASSED JSON and unchanged original templates |
| Fail before execution | `tests/test_integration/test_integration_static_variables.py::test_invalid_template_fails_before_executor` | Three invalid fields raise; no CSV or report appears. Does not directly spy on executor/watchdog start |
| Load-time recursion failure | `tests/test_integration/test_integration_static_variables.py::test_config_rejects_recursive_variable` | Actual ConfigLoader and generated YAML |
| Separate run directories | `tests/test_integration/test_integration_static_variables.py::test_two_runs_resolve_distinct_run_dirs` | Two actual runs each contain CSV; not a concurrent directory uniqueness test |
| Report version | `tests/test_unit/test_runner.py::test_cancellation_lifecycle_and_summary`, `tests/test_integration/test_integration.py::test_yaml_to_result_json`, `tests/test_integration/test_integration.py::test_integration_stops_after_failed_step`, `tests/test_integration/test_integration_artifact_validation.py::test_csv_and_json_content_validation` | Explicit report assertions synchronized to 1.7.0; actual function names are checked during documentation validation |

## AI collaboration and regression fixes

The session records AI changes to timeout support, integration fixtures, documentation and descriptions. Source authorship outside this record is not inferred.

| Original gap or failure | Change and regression evidence | Remaining boundary |
| --- | --- | --- |
| Timeout condition rejected ints and compared unsupported values | Accept exact int/float with positive/finite checks; positive and invalid timeout parameterized tests | Decimal and numeric subclasses are intentionally unsupported |
| Positive float 3.5 was listed as invalid | Move positive floats to acceptance cases, retain exact type assertions | Fractional timeout interruption is not directly tested by the static-variable integration suite |
| f-string consumed double braces; script and first argument lacked whitespace | Use an ordinary template string with leading space; YAML-to-report and two-run cases execute real subprocesses | Shell injection/quoting for arbitrary variable input is not tested |
| json.load received report text | Use json.loads; end-to-end JSON assertions guard the call | Does not alter production reporter schema |
| Report metadata still identified 1.6.3 | Synchronize runtime and explicit version expectations | Installed distribution version and release publication remain separate checks |
| New variable tests lacked Given/When/Then | Add concrete descriptions; audit all test functions and compare executable AST against staged inputs | Description counts alone cannot prove assertion quality |

## Gaps

Source inspection confirms eager resolution across all stages and rules. Dedicated static-variable tests do not cover every cleanup stage, retry interaction, malformed definition variant, unsupported dataclass, YAML null variables, arbitrary field exclusion, or subprocess quoting input. Full-suite success is local evidence; Linux CI, detached processes, real CLI signals and release state are not established here.
