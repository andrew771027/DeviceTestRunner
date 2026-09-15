# Device Test Runner v1.5.2 Acceptance Criteria

## Scope

Failure Classification.

Version baseline: implementation and verification record described below.

This document preserves the recorded acceptance state for this version. Test results and release checks below are historical records; they have not been rerun or reverified by this formatting update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | a command exits successfully and its step-scoped artifact rules pass | the runner completes the attempt | the attempt is successful, its failure type is `NONE`, and no retry occurs. |
| AC-2 | a command runs longer than `timeout_second` | the executor stops the process | the attempt is classified as `TIMEOUT`, available stdout／stderr is preserved, and retry follows the configured limit. |
| AC-3 | a failed command reports a supported offline, missing-device, or unauthorized-device message | process failure is classified | the attempt is classified as `DEVICE_OFFLINE` rather than a generic process error. |
| AC-4 | a command fails without timeout or a recognized device-offline pattern | process failure is classified | the attempt is classified as `PROCESS_ERROR`, and its exit code and diagnostic logs remain available. |
| AC-5 | a required artifact does not exist after a successful command | a retry-enabled rule validates that artifact | the attempt is classified as `ARTIFACT_MISSING` and may retry while attempt capacity remains. |
| AC-6 | an artifact exists but violates its configured validation contract | validation runs | the result is classified as `ARTIFACT_INVALID` with a diagnostic validation message. |
| AC-7 | more than one failure signal is available | the runner determines the attempt failure type | process failure takes precedence over artifact failure, and a missing artifact takes precedence over an invalid artifact. |
| AC-8 | an attempt has a retryable failure type | its number is below `max_attempts` | another attempt is allowed after the configured delay; at `max_attempts`, retry stops. |
| AC-9 | a test run contains one or more attempts | `result.json` is generated | each attempt records success, failure type, exit code, duration, stdout／stderr paths, executor error, and artifact validation results. |
| AC-10 | a setup or scenario step ultimately fails | retry is exhausted or disallowed | later protected work is skipped, teardown guarantees are honored, and final run status is `FAILED`. |

## Verification

- [x] Unit and integration coverage maps to AC-1 through AC-10.
- [x] Full suite passes: 112 tests.
- [x] Runner and report metadata identify version `1.5.2`.
- [x] Architecture and test matrix are documented.
- [ ] Release tag `v1.5.2` is created.

Related records: [Test matrix](../test_matrix/test_matrix_v1.5.2.md) · [Definition of done](../definition_of_done/definition_of_done_v1.5.2.md).

## Acceptance decision

code and repository documentation satisfy v1.5.2 acceptance criteria; release publication remains pending until the tag and GitHub Release are created.
