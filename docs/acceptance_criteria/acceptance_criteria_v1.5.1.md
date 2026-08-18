# Device Test Runner v1.5.1 Acceptance Criteria

Baseline: current working tree after tag `v1.5.0` (release candidate)

- [x] Validation rules support optional `after_step` and `retry_on_failure` fields.
- [x] Only `retry_on_failure: true` rules associated with the current step participate in attempt-level validation.
- [x] A command-success/artifact-failure attempt is recorded as failed and can retry.
- [x] A later attempt can pass when both command and associated artifact rules pass.
- [x] Artifact retry exhaustion fails the step and stops later scenario steps.
- [x] Rules without retry opt-in remain final validations and can fail the run without retrying the step.
- [x] Per-attempt artifact validation results are serialized into `result.json`.
- [ ] Retry artifact cleanup is called by the runner and its file/directory tests pass.
- [ ] The real artifact-aware integration fixture is valid and passes.
- [ ] The complete test suite passes with no failures.
- [ ] Version `v1.5.1` is tagged after all release checks complete.

Release decision: Not yet accepted. Last targeted run was 24 passed and 2 failed.
