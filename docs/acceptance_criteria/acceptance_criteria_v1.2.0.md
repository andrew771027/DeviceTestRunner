# Device Test Runner v1.2.0 Acceptance Criteria

## Scope

Artifact management.

Version baseline: Git tag `v1.2.0`

This document preserves the recorded acceptance state for this version. Test results and release checks below are historical records; they have not been rerun or reverified by this formatting update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | A configured test | A run starts | Every run creates an identifiable artifact directory. |
| AC-2 | Command stdout and stderr | The runner saves artifacts | stdout and stderr can be persisted as artifacts. |
| AC-3 | A completed run | The execution result is inspected | The execution result exposes its artifact directory and metadata. |
| AC-4 | A configured command | The runner delegates execution | `SubprocessExecutor` is the command execution abstraction. |
| AC-5 | The sample configuration | The runner executes the artifact and report pipeline | The sample configuration completes through the artifact/report pipeline. |

## Verification

- [x] AC-1 through AC-5 are marked complete in the recorded baseline.

Related records: [Test matrix](../test_matrix/test_matrix_v1.2.0.md) · [Definition of done](../definition_of_done/definition_of_done_v1.2.0.md).

## Acceptance decision

Accepted at Git tag `v1.2.0`, as recorded in the original acceptance checklist.
