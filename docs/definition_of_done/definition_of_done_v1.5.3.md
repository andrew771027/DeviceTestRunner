# Device Test Runner v1.5.3 Definition of Done

Release theme: Selective Retry and Artifact Criticality

## Product and Architecture

- [x] `retry.retry_on` controls retry by `FailureType`.
- [x] Missing `retry_on` defaults to no retry; invalid values are rejected and duplicates removed.
- [x] Artifact `required` defaults to `true` and optional failures remain diagnostic-only.
- [x] Retry cleanup is restricted to required targets inside the run directory.
- [x] `result.json` records artifact criticality and `failed_required_artifact_rules`.
- [x] Runner metadata version is `1.5.3`.

## Quality

- [x] Unit tests cover configuration, policy allow-list, runner decisions, cleanup safety, summary and serialization.
- [x] Integration tests cover real artifact-aware retry and v1.5.3 report metadata.
- [x] Existing lifecycle, validation and failure-classification coverage remains green.
- [x] Full suite passes: 134 tests on 2026-09-04.

## Documentation and Release

- [x] README documents v1.5.3 configuration and behavior.
- [x] Architecture, Test Matrix and Acceptance Criteria v1.5.3 are created.
- [x] Roadmap includes the completed v1.5.3 milestone.
- [x] CHANGELOG records v1.5.3.
- [ ] Test Case Description is reviewed for v1.5.3.
- [ ] Git tag `v1.5.3` is created.
- [ ] GitHub Release notes are published.

Release readiness: requested product documentation and verified implementation are complete. The remaining unchecked release-governance items follow `CommitManual.md` and were outside this request.
