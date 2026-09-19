# Device Test Runner v1.1.0 Acceptance Criteria

## Scope

Naming and model refactoring.

Version baseline: Git tag `v1.1.0`

Historical acceptance record. Tests and release checks were not rerun for this editorial update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | Test-domain classes | pytest discovers tests | Test-domain classes use names that do not collide with pytest discovery. |
| AC-2 | A configured test | Configuration passes through the loader, models, executor and runner | YAML keys, loader output, models, executor, and runner use consistent naming. |
| AC-3 | An existing v1.0 configuration | The refactored runner executes it | Existing v1.0 configurations remain executable after the refactor. |
| AC-4 | A completed command | The runner creates a step result | Step results preserve command outcome and output. |
| AC-5 | The tagged baseline | Unit and integration tests run | Refactored unit and integration tests pass for the tagged baseline. |

## Verification

- [x] AC-1 through AC-5 are marked complete in the recorded baseline.

Related records: [Test matrix](../test_matrix/test_matrix_v1.1.0.md) · [Definition of done](../definition_of_done/definition_of_done_v1.1.0.md).

## Acceptance decision

Accepted at Git tag `v1.1.0`, as recorded in the original acceptance checklist.
