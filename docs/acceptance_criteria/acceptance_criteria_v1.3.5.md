# Device Test Runner v1.3.5 Acceptance Criteria

Baseline: Git tag `v1.3.5`

- [x] Command stdout is streamed to the console when console output is enabled.
- [x] Command stderr is streamed without being merged into stdout.
- [x] stdout and stderr are simultaneously persisted to artifact logs.
- [x] Log writes are flushed promptly for live diagnostics.
- [x] Failure results retain complete output and artifact paths.
- [x] Lifecycle behavior from v1.3.0 remains unchanged.

Release decision: Accepted by tag `v1.3.5`.
