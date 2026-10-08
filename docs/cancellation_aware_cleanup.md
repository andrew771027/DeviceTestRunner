# Cancellation-Aware Cleanup

**Device Test Runner v1.6.3**

## Overview

Device Test Runner v1.6.3 introduces a dedicated cleanup execution scope.

Cancellation stops normal test execution but does not automatically cancel teardown.

Cleanup uses its own cancellation token and may have an independent timeout.

```text
Run Scope
    |
    | cancellation
    v
Stop Normal Work
    |
    v
Cleanup Scope
    |
    +-- teardown
    |
    +-- global_teardown
    |
    v
Artifact Validation
    |
    v
Final Report
```

`teardown` runs only when `global_setup` completed successfully. `global_teardown` is attempted even if the run was cancelled before setup or global setup failed, provided the cleanup token has not been cancelled.

For attempt-level process termination and its limitations, see [Process Lifecycle](process_lifecycle.md). Version planning is recorded in the [Roadmap](roadmap.md#v163--cancellation-aware-cleanup).

## Configuration

```yaml
run_timeout_seconds: 3600
cleanup_timeout_seconds: 60
```

Omitting `cleanup_timeout_seconds` leaves the cleanup scope without an overall timeout. Individual cleanup steps retain their own step timeout:

```yaml
lifecycle:
  teardown:
    steps:
      - name: stop_recorder
        type: command
        command: bash stop_recorder.sh
        timeout_second: 20
```

## Timeout Scopes

Device Test Runner has three distinct timeout scopes.

| Timeout | Scope | Result |
| --- | --- | --- |
| Step timeout | One step attempt | `FailureType.TIMEOUT` |
| Run timeout | Normal run | Run cancellation with `run_timeout` |
| Cleanup timeout | Cleanup lifecycle | Cleanup cancellation with `cleanup_timeout` |

A step timeout does not mean that the cleanup scope has timed out.

A cleanup timeout does not overwrite the original run cancellation reason.

## Independent Cleanup Scope

The run and cleanup lifecycle use separate cancellation tokens.

```text
RunCancellationToken
        |
        +-- global_setup
        +-- setup
        +-- scenario

CleanupCancellationToken
        |
        +-- teardown
        +-- global_teardown
```

This allows cleanup to run after the run token has already been cancelled. Cleanup attempts and retry delays share the cleanup token.

## Cleanup Timeout

`cleanup_timeout_seconds` is a shared time budget for the cleanup scope.

For example:

```yaml
cleanup_timeout_seconds: 60
```

If teardown consumes 55 seconds, only approximately five seconds remain for subsequent cleanup work.

When the cleanup deadline is reached:

1. The cleanup cancellation token is cancelled.
2. The currently running cleanup process is terminated through the managed process lifecycle.
3. Remaining cleanup steps are not started.
4. The cleanup result is recorded in the final report.

Process termination and output draining may extend beyond the deadline. Final artifact validation and reporting occur after the cleanup scope and are outside its timeout budget.

## Best-Effort Cleanup

A normal teardown step failure does not immediately stop all cleanup.

For example:

```text
stop_recorder
    |
    | Step TIMEOUT
    v
record failure
    |
    v
release_device
    |
    v
global_teardown
```

This behavior allows cleanup to release as many resources as possible.

The cleanup-scope timeout is different: once the cleanup scope itself is cancelled, no new cleanup work is started.

## Partial Artifacts

Cancellation may leave incomplete or missing artifacts.

Device Test Runner still performs final artifact validation. Cancelled attempts skip attempt-level validation and are not retried.

Example:

```text
Expected:
    power.csv
    summary.json
    debug.log

After cancellation:
    power.csv      partial
    summary.json   missing
    debug.log      valid
```

These results are preserved individually in the report.

Artifact validation does not replace the primary cancellation reason.

For example:

```text
Run Timeout
    +
power.csv invalid
    +
summary.json missing

Final Run Status:
    TIMED_OUT
```

The artifact validation results remain available for diagnosis.

## Status Priority

Run-level termination reason has priority over cleanup and artifact failures. Status is calculated in this order:

```text
RUN_TIMEOUT
    → TIMED_OUT

USER_REQUEST
    → CANCELLED

Cleanup failure
    → FAILED

Cancelled steps
    → CANCELLED

Execution failure or skipped steps
    → FAILED

Required artifact failure
    → FAILED

Otherwise
    → PASSED
```

For example:

```text
Run Timeout
    |
    v
Cleanup Timeout
    |
    v
Partial Artifact Failure
```

The final status remains:

```text
TIMED_OUT
```

The report separately records the cleanup timeout and artifact failures.

## Reporting

Example of the relevant report fields for a v1.6.3 run:

```json
{
  "metadata": {
    "runner_version": "1.6.3",
    "cancel_requested": true,
    "cancel_reason": "run_timeout",
    "run_timed_out": true,
    "run_timeout_seconds": 3600
  },
  "summary": {
    "status": "TIMED_OUT"
  },
  "cleanup_summary": {
    "attempted": true,
    "timed_out": false,
    "failed": false,
    "cancellation_reason": null
  }
}
```

`runner_version` reflects the runtime version. `cleanup_timeout_seconds` is currently a configuration field and is not serialized in report metadata. Cleanup timeout outcomes are recorded in `cleanup_summary`.

## Design Principle

Cancellation means:

> Stop normal work and transition into cleanup.

It does not mean:

> Immediately stop every activity in the runner.

Cleanup is itself a managed execution scope with its own cancellation token, timeout, process lifecycle, results, and reporting.

## Version History

- v1.6.0 — Cancellation Foundation
- v1.6.1 — Safe Process Termination
- v1.6.2 — Run-Level Timeout
- v1.6.3 — Cancellation-Aware Cleanup

v1.6.3 establishes the cleanup safety foundation.

More flexible lifecycle hooks, custom pre/post hooks, and richer failure-aware teardown behavior remain separate concerns for later lifecycle versions.
