# Device Test Runner v1.4.0 Acceptance Criteria

Baseline: Git tag `v1.4.0`

- [x] YAML can configure named artifact validation rules.
- [x] File existence, file size, extension, and non-empty directory rules are evaluated.
- [x] Missing or invalid targets return explicit failed validation results.
- [x] All validation results are aggregated into `RunResult` and `result.json`.
- [x] Any failed final artifact rule makes the run status `FAILED`.
- [x] Unit and integration tests cover passing and failing artifacts.

Release decision: Accepted by tag `v1.4.0`.
