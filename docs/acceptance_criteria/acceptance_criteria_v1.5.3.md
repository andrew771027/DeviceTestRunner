# Device Test Runner v1.5.3 Acceptance Criteria

## Scope

Selective Retry and Artifact Criticality.

Version baseline: implementation and verification record described below.

Historical acceptance record. Tests and release checks were not rerun for this editorial update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | `retry.retry_on` contains a failure type and attempts remain | an attempt ends with that type | the runner waits for the configured delay and retries. |
| AC-2 | a failure type is absent from `retry_on` | an attempt fails with that type | the runner stops the step without consuming additional attempts. |
| AC-3 | `retry_on` contains duplicates, an unknown value, or `none` | configuration is loaded | duplicates are removed in order, while unknown values and `none` are rejected. |
| AC-4 | an artifact rule omits `required` | configuration is loaded | the rule is treated as required. |
| AC-5 | a required artifact is missing or invalid | its rule is evaluated | the attempt or final run fails and retry only occurs when its failure type is configured. |
| AC-6 | an optional artifact is missing or invalid | validation runs | the failed result remains observable, but does not fail the step or run and does not trigger retry. |
| AC-7 | retry is allowed after required artifact failure | targets are prepared for another attempt | only required targets inside the run directory are removed; optional, missing, and external targets remain safe. |
| AC-8 | validation has completed | `result.json` is generated | each result exposes `required`, summary separates all failed rules from failed required rules, and metadata reports `1.5.3`. |

## Verification

- [x] Unit and integration coverage maps to AC-1 through AC-8.
- [x] Full suite passes: 134 tests on 2026-09-04.
- [x] Runner and report metadata identify version `1.5.3`.
- [x] README, Architecture, Test Matrix, Acceptance Criteria, Definition of Done and Roadmap are updated.
- [x] CHANGELOG records v1.5.3.
- [ ] Release tag `v1.5.3` is created.

Related records: [Test matrix](../test_matrix/test_matrix_v1.5.3.md) · [Definition of done](../definition_of_done/definition_of_done_v1.5.3.md).

## Acceptance decision

implementation, tests, sample configuration, changelog, and requested documentation satisfy the v1.5.3 functional criteria; release publication remains pending under `CommitManual.md`.
