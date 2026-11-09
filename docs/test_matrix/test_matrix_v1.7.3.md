# Device Test Runner v1.7.3 Test Matrix

Scope: configuration validation; source f56a44b, tests ed6cf39 and current working tree. See [pytest techniques](../test_guide.md#v1-7-3) and [execution record](../definition_of_done/definition_of_done_v1.7.3.md).

## Requirement coverage

Unless specified otherwise, functions below are in tests/test_unit/test_configuration_validation.py.

| Requirement | Test function | Direct assertion / boundary |
| --- | --- | --- |
| Valid schema and deferred timeout | test_valid_schema | Env/vars templates and omitted lifecycle stages accepted; no template evaluation |
| Invalid scalars, keys and collections | test_invalid_schema | 13 mutations reject bool max_attempts, negative delay/rows, zero/string timeout, string required/columns, unknown keys, missing device, non-list steps, bool run timeout and infinite variable |
| Phase aggregation | test_schema_aggregates_multiple_errors | At least two errors stored; does not assert exact order or every message |
| Semantic constraints | test_invalid_cross_fields | Six cases: missing step, unsupported rule type, reversed size bounds, missing extension/CSV/JSON constraints; size case also has unsupported type |
| Unique artifact names | test_duplicate_rule_names_rejected | Duplicate rule name raises |
| Cleanup reference rejected | test_cleanup_after_step_rejected | teardown reference rejected; global_teardown branch inspected in source |
| Valid CSV constraint | test_valid_cross_field | required_columns alone accepted |
| Loader wiring | test_loader_validates_schema_and_cross_fields | Writes YAML, preserves timeout template, then mutates after_step and expects unknown step |
| Invalid mappings | test_non_mapping_values_report_validation_errors | 11 locations × four values = 44 cases, including direct schema root; loader root has separate ValueError contract |
| Scope timeouts | test_invalid_run_and_cleanup_timeouts | Two fields × five invalid values = 10 cases; minimum 1e-8 boundary not directly tested |
| Existing loader behavior | tests/test_unit/test_config_loader.py | Updated retry message assertions and optional-timeout helper calls |
| Real subprocess working directory | tests/test_integration/test_integration_artifact_validation.py::test_command_runs_inside_run_directory | Corrected timeout_second, validation and exists fixture fields; current_directory.txt and run directory assertions |

The configuration-validation module contains 10 test functions collecting 79 cases. Parameterization expands function counts. Current suite totals and verification are recorded in the completion record.

## Corrections and collaboration

The draft loader test used == instead of assignment when changing after_step, so its expected error could never be exercised. The existing working-tree assignment fixes the test setup; no product behavior change is attributed to this documentation task. Artifact integration fixture typos formerly ignored now cause schema failures; their corrections restore the intended working-directory test. Retry error text assertions follow the new schema diagnostics. Calls to the misspelled optional-timeout helper now use the actual helper name.

This documentation task adds Given/When/Then descriptions without changing executable test AST. Original test authorship is not inferred from Git history. No new behavioral tests are claimed.

## Inspected behavior and gaps

Global step-name uniqueness, unsupported step types, global_teardown after_step, all nested unknown-key combinations, null/default combinations, whitespace strings, list item types, valid JSON/extension paths and exact numeric boundary coverage are not all directly asserted by this module. Source checks cover these policies; existing regression suites are separate evidence, not proof of every validator branch. No CLI invalid-config exit-code/report test, real hardware, external Android demo execution, Windows or release publication is established.
