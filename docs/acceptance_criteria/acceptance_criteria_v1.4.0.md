# Device Test Runner v1.4.0 Acceptance Criteria

## Scope

Artifact validation.

Version baseline: Git tag `v1.4.0`

This document preserves the recorded acceptance state for this version. Test results and release checks below are historical records; they have not been rerun or reverified by this formatting update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | Named artifact validation rules in YAML | The loader reads the configuration | YAML can configure named artifact validation rules. |
| AC-2 | Existence, size, extension and non-empty directory rules | The validator evaluates their targets | File existence, file size, extension, and non-empty directory rules are evaluated. |
| AC-3 | A missing or invalid target | Its validation rule runs | Missing or invalid targets return explicit failed validation results. |
| AC-4 | Completed artifact validations | The runner builds the report | All validation results are aggregated into `RunResult` and `result.json`. |
| AC-5 | A failed final artifact rule | The runner determines final status | Any failed final artifact rule makes the run status `FAILED`. |
| AC-6 | Passing and failing artifacts | Unit and integration coverage is reviewed | Unit and integration tests cover passing and failing artifacts. |

## Verification

- [x] AC-1 through AC-6 are marked complete in the recorded baseline.

Related records: [Test matrix](../test_matrix/test_matrix_v1.4.0.md) · [Definition of done](../definition_of_done/definition_of_done_v1.4.0.md).

## Acceptance decision

Accepted at Git tag `v1.4.0`, as recorded in the original acceptance checklist.
