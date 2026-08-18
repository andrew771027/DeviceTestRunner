# Device Test Runner v1.5.0 Acceptance Criteria

Baseline: Git tag `v1.5.0`

- [x] YAML accepts `retry.max_attempts` and `retry.delay_seconds`.
- [x] Missing retry configuration defaults to one attempt and zero delay.
- [x] Invalid retry limits or delays fail configuration loading.
- [x] Failed commands retry until success or the configured maximum.
- [x] Successful commands are not retried.
- [x] Every attempt retains its own result and stdout/stderr log files.
- [x] Retry exhaustion fails the step and preserves lifecycle failure handling.

Release decision: Accepted by tag `v1.5.0`.
