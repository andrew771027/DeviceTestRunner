# Device Test Runner v1.5.3 Acceptance Criteria

Release theme: Selective Retry and Artifact Criticality

## AC-1 — Explicit retry selection

**Given** `retry.retry_on` contains a failure type and attempts remain
**When** an attempt ends with that type
**Then** the runner waits for the configured delay and retries.

## AC-2 — Unconfigured failure

**Given** a failure type is absent from `retry_on`
**When** an attempt fails with that type
**Then** the runner stops the step without consuming additional attempts.

## AC-3 — Retry configuration validation

**Given** `retry_on` contains duplicates, an unknown value, or `none`
**When** configuration is loaded
**Then** duplicates are removed in order, while unknown values and `none` are rejected.

## AC-4 — Required artifact default

**Given** an artifact rule omits `required`
**When** configuration is loaded
**Then** the rule is treated as required.

## AC-5 — Required artifact failure

**Given** a required artifact is missing or invalid
**When** its rule is evaluated
**Then** the attempt or final run fails and retry only occurs when its failure type is configured.

## AC-6 — Optional artifact failure

**Given** an optional artifact is missing or invalid
**When** validation runs
**Then** the failed result remains observable, but does not fail the step or run and does not trigger retry.

## AC-7 — Safe retry cleanup

**Given** retry is allowed after required artifact failure
**When** targets are prepared for another attempt
**Then** only required targets inside the run directory are removed; optional, missing, and external targets remain safe.

## AC-8 — Report traceability

**Given** validation has completed
**When** `result.json` is generated
**Then** each result exposes `required`, summary separates all failed rules from failed required rules, and metadata reports `1.5.3`.

## Release Evidence

* [x] Unit and integration coverage maps to AC-1 through AC-8.
* [x] Full suite passes: 134 tests on 2026-09-04.
* [x] Runner and report metadata identify version `1.5.3`.
* [x] README, Architecture, Test Matrix, Acceptance Criteria, Definition of Done and Roadmap are updated.
* [x] CHANGELOG records v1.5.3.
* [ ] Release tag `v1.5.3` is created.

Acceptance decision: implementation, tests, sample configuration, changelog, and requested documentation satisfy the v1.5.3 functional criteria; release publication remains pending under `CommitManual.md`.
