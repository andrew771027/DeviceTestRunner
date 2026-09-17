# Device Test Runner v1.0.0 Acceptance Criteria

## Scope

Basic YAML runner.

Version baseline: Git tag `v1.0.0`

Historical acceptance record. Tests and release checks were not rerun for this editorial update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | A valid YAML configuration | The loader reads the file | A valid YAML file loads into the configured test and device models. |
| AC-2 | Configured command steps | The runner executes the test | The runner executes configured command steps through a subprocess executor. |
| AC-3 | A completed command | The executor returns its result | Exit code, stdout, stderr, and basic step status are returned. |
| AC-4 | An execution result | The report is saved | A JSON execution result can be produced. |
| AC-5 | The configuration-to-result path | Test coverage is reviewed | Unit and integration tests exist for the configuration-to-result path. |

## Verification

- [x] AC-1 through AC-5 are marked complete in the recorded baseline.

Related records: [Test matrix](../test_matrix/test_matrix_v1.0.0.md) · [Definition of done](../definition_of_done/definition_of_done_v1.0.0.md).

## Acceptance decision

Accepted at Git tag `v1.0.0`, as recorded in the original acceptance checklist.
