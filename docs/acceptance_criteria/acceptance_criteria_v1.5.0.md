# Device Test Runner v1.5.0 Acceptance Criteria

## Scope

Retry policy.

Version baseline: Git tag `v1.5.0`

This document preserves the recorded acceptance state for this version. Test results and release checks below are historical records; they have not been rerun or reverified by this formatting update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | Retry limits and delay in YAML | The loader reads the configuration | YAML accepts `retry.max_attempts` and `retry.delay_seconds`. |
| AC-2 | No retry configuration | The loader applies defaults | Missing retry configuration defaults to one attempt and zero delay. |
| AC-3 | Invalid retry limits or delays | The loader validates the configuration | Invalid retry limits or delays fail configuration loading. |
| AC-4 | A failed command with attempts remaining | The runner evaluates retry | Failed commands retry until success or the configured maximum. |
| AC-5 | A successful command | The runner evaluates retry | Successful commands are not retried. |
| AC-6 | One or more attempts | The runner saves execution results | Every attempt retains its own result and stdout/stderr log files. |
| AC-7 | A step has exhausted its attempts | The runner handles the final failure | Retry exhaustion fails the step and preserves lifecycle failure handling. |

## Verification

- [x] AC-1 through AC-7 are marked complete in the recorded baseline.

Related records: [Test matrix](../test_matrix/test_matrix_v1.5.0.md) · [Definition of done](../definition_of_done/definition_of_done_v1.5.0.md).

## Acceptance decision

Accepted at Git tag `v1.5.0`, as recorded in the original acceptance checklist.
