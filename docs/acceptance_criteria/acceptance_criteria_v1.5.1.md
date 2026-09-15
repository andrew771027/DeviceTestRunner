# Device Test Runner v1.5.1 Acceptance Criteria

## Scope

Artifact-aware retry.

Historical baseline: the working tree after tag `v1.5.0` (release candidate)

This document preserves the recorded acceptance state for this version. Test results and release checks below are historical records; they have not been rerun or reverified by this formatting update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | Validation rules with optional step and retry fields | The loader reads the configuration | Validation rules support optional `after_step` and `retry_on_failure` fields. |
| AC-2 | Rules associated with different steps and retry settings | The runner selects attempt-level rules | Only `retry_on_failure: true` rules associated with the current step participate in attempt-level validation. |
| AC-3 | A successful command with failed retry-enabled artifact validation | The runner evaluates the attempt | A command-success/artifact-failure attempt is recorded as failed and can retry. |
| AC-4 | A later attempt with successful command and artifact validation | The runner evaluates the attempt | A later attempt can pass when both command and associated artifact rules pass. |
| AC-5 | Artifact validation fails through the retry limit | The runner handles exhaustion | Artifact retry exhaustion fails the step and stops later scenario steps. |
| AC-6 | Rules without retry opt-in | The runner performs final validation | Rules without retry opt-in remain final validations and can fail the run without retrying the step. |
| AC-7 | Per-attempt validation results | The runner writes the report | Per-attempt artifact validation results are serialized into `result.json`. |

## Verification

- [x] AC-1 through AC-7 are marked complete in the recorded baseline.
- [ ] Retry artifact cleanup is called by the runner and its file/directory tests pass.
- [ ] The real artifact-aware integration fixture is valid and passes.
- [ ] The complete test suite passes with no failures.
- [ ] Version `v1.5.1` is tagged after all release checks complete.

Recorded targeted test result: **24 passed, 2 failed**.

Related records: [Test matrix](../test_matrix/test_matrix_v1.5.1.md) · [Definition of done](../definition_of_done/definition_of_done_v1.5.1.md).

## Acceptance decision

Not yet accepted. The remaining checks above must pass before release acceptance.
