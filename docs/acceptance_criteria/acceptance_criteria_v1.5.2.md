# Device Test Runner v1.5.2 Acceptance Criteria

Release theme: Failure Classification

## AC-1 — Successful attempt

**Given** a command exits successfully and its step-scoped artifact rules pass
**When** the runner completes the attempt
**Then** the attempt is successful, its failure type is `NONE`, and no retry occurs.

## AC-2 — Timeout failure

**Given** a command runs longer than `timeout_second`
**When** the executor stops the process
**Then** the attempt is classified as `TIMEOUT`, available stdout／stderr is preserved, and retry follows the configured limit.

## AC-3 — Device offline failure

**Given** a failed command reports a supported offline, missing-device, or unauthorized-device message
**When** process failure is classified
**Then** the attempt is classified as `DEVICE_OFFLINE` rather than a generic process error.

## AC-4 — Generic process failure

**Given** a command fails without timeout or a recognized device-offline pattern
**When** process failure is classified
**Then** the attempt is classified as `PROCESS_ERROR`, and its exit code and diagnostic logs remain available.

## AC-5 — Missing artifact

**Given** a required artifact does not exist after a successful command
**When** a retry-enabled rule validates that artifact
**Then** the attempt is classified as `ARTIFACT_MISSING` and may retry while attempt capacity remains.

## AC-6 — Invalid artifact

**Given** an artifact exists but violates its configured validation contract
**When** validation runs
**Then** the result is classified as `ARTIFACT_INVALID` with a diagnostic validation message.

## AC-7 — Failure priority

**Given** more than one failure signal is available
**When** the runner determines the attempt failure type
**Then** process failure takes precedence over artifact failure, and a missing artifact takes precedence over an invalid artifact.

## AC-8 — Retry boundary

**Given** an attempt has a retryable failure type
**When** its number is below `max_attempts`
**Then** another attempt is allowed after the configured delay; at `max_attempts`, retry stops.

## AC-9 — Report traceability

**Given** a test run contains one or more attempts
**When** `result.json` is generated
**Then** each attempt records success, failure type, exit code, duration, stdout／stderr paths, executor error, and artifact validation results.

## AC-10 — Lifecycle behavior

**Given** a setup or scenario step ultimately fails
**When** retry is exhausted or disallowed
**Then** later protected work is skipped, teardown guarantees are honored, and final run status is `FAILED`.

## Release Evidence

- [x] Unit and integration coverage maps to AC-1 through AC-10.
- [x] Full suite passes: 112 tests.
- [x] Runner and report metadata identify version `1.5.2`.
- [x] Architecture and test matrix are documented.
- [ ] Release tag `v1.5.2` is created.

Acceptance decision: code and repository documentation satisfy v1.5.2 acceptance criteria; release publication remains pending until the tag and GitHub Release are created.
