# Device Test Runner v1.3.0 Acceptance Criteria

## Scope

Test lifecycle.

Version baseline: Git tag `v1.3.0`

This document preserves the recorded acceptance state for this version. Test results and release checks below are historical records; they have not been rerun or reverified by this formatting update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | A configured lifecycle | The runner executes its stages | Lifecycle stages execute in the order `global_setup` → `setup` → `scenario` → `teardown` → `global_teardown`. |
| AC-2 | A successful lifecycle | The runner aggregates results | A successful lifecycle records every configured step. |
| AC-3 | A failed scenario step | The runner selects the next step | Scenario failure prevents later scenario steps from running. |
| AC-4 | A lifecycle failure | The runner routes cleanup | Teardown and global teardown behavior follows the documented failure path. |
| AC-5 | A completed lifecycle | The runner builds the report | Configured, executed, passed, failed, and skipped steps are reportable. |
| AC-6 | Success and failure routes | Test coverage is reviewed | Unit and integration coverage exercises success and failure routing. |

## Verification

- [x] AC-1 through AC-6 are marked complete in the recorded baseline.

Related records: [Test matrix](../test_matrix/test_matrix_v1.3.0.md) · [Definition of done](../definition_of_done/definition_of_done_v1.3.0.md).

## Acceptance decision

Accepted at Git tag `v1.3.0`, as recorded in the original acceptance checklist.
