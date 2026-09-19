# Device Test Runner v1.3.5 Acceptance Criteria

## Scope

Command output streaming.

Version baseline: Git tag `v1.3.5`

Historical acceptance record. Tests and release checks were not rerun for this editorial update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | Console output is enabled | A command writes stdout | Command stdout is streamed to the console when console output is enabled. |
| AC-2 | A command writes stderr | The executor streams output | Command stderr is streamed without being merged into stdout. |
| AC-3 | A command produces output | The executor streams and saves it | stdout and stderr are simultaneously persisted to artifact logs. |
| AC-4 | An active log writer | New output is written | Log writes are flushed promptly for live diagnostics. |
| AC-5 | A failed command | The runner records its result | Failure results retain complete output and artifact paths. |
| AC-6 | A v1.3.0 lifecycle configuration | The updated executor runs its steps | Lifecycle behavior from v1.3.0 remains unchanged. |

## Verification

- [x] AC-1 through AC-6 are marked complete in the recorded baseline.

Related records: [Test matrix](../test_matrix/test_matrix_v1.3.5.md) · [Definition of done](../definition_of_done/definition_of_done_v1.3.5.md).

## Acceptance decision

Accepted at Git tag `v1.3.5`, as recorded in the original acceptance checklist.
