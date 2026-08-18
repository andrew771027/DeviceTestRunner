# Device Test Runner v1.5.1 Definition of Done

Baseline: current working tree after tag `v1.5.0` (release candidate)

- [x] `after_step` and `retry_on_failure` are represented in config and models.
- [x] Runner selects retry-enabled validation rules by step.
- [x] Attempt success combines command and associated artifact outcomes.
- [x] Per-attempt artifact validation results are represented in the report model.
- [x] Unit coverage exists for recovery, exhaustion, non-retryable rules, and filtering.
- [x] README, changelog, roadmap, and v1.5.1 release documentation are prepared.
- [ ] Artifact cleanup API and tests agree on the rule collection contract.
- [ ] Artifact cleanup is integrated into the retry lifecycle if it is part of the release scope.
- [ ] The artifact-aware integration YAML fixture parses and its assertions use the correct attempt result.
- [ ] Unit and integration suites pass without failures.
- [ ] Architecture filename/version convention is finalized (`architecture_v.1.5.1.md` versus existing `architecture_v1.x.x.md`).
- [ ] Commit checklist is complete and tag `v1.5.1` is created.

Status: Not done. Last targeted run was 24 passed and 2 failed; no `v1.5.1` tag exists.
