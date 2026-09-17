# Device Test Runner v1.6.0 Acceptance Criteria

## Scope

Cancellation Foundation.

Version baseline: implementation and verification record described below.

Historical acceptance record. Tests and release checks were not rerun for this editorial update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | a new token shared with the runner | a caller requests cancellation, including repeated requests | the token stays cancelled; `raise_if_cancelled()` raises `CancellationRequested`, while it does nothing on an active token. |
| AC-2 | a command is still running with an active token | the executor observes cancellation during polling | it stops the direct process, preserves captured output and returns `cancelled=true`, `timed_out=false`, `failure_type=cancelled`. |
| AC-3 | a command remains running beyond `timeout_second` without cancellation | the executor observes timeout | it reports `timed_out=true`, `cancelled=false` and `failure_type=timeout`. |
| AC-4 | cancellation is reported with attempt capacity remaining | runner or retry policy evaluates another attempt | no retry occurs; YAML `retry_on` rejects `cancelled`, and direct Python policy also refuses it even if explicitly listed. |
| AC-5 | a failed normal step is waiting before retry | its token becomes cancelled | polling ends the delay, no next attempt starts, and the step is marked cancelled while prior attempt evidence remains unchanged. |
| AC-6 | cancellation occurs before run, during global_setup, or after entering setup/scenario | the runner routes the remaining controlled lifecycle | pre-run/global_setup cancellation reaches global_teardown only, while setup/scenario cancellation reaches both cleanup stages; cleanup receives a fresh active execution token. |
| AC-7 | a cancelled attempt has required artifact rules | the runner finalizes the run | attempt-level validation is skipped, all rules are still evaluated at run end, and required artifact failure does not override CANCELLED status. |
| AC-8 | cancellation was requested or a step was marked cancelled | the runner writes `result.json` | metadata reports runtime `1.6.0` and `cancel_requested`, attempts expose cancellation/timeout flags, summary separates `cancelled_steps` from `failed_steps`, and final status is CANCELLED. |

## Verification

- [x] Unit and integration evidence maps to AC-1 through AC-8; boundaries are recorded in the Test Matrix.
- [x] All 150 test functions have reviewed Given／When／Then descriptions; executable test AST is unchanged.
- [x] Runtime source version is `1.6.0`.
- [x] README, Architecture, Test Matrix, Acceptance Criteria, Definition of Done, Roadmap and CHANGELOG are updated.
- [x] Distribution version in `pyproject.toml` is synchronized to `1.6.0`.
- [ ] Sample configuration completes with PASSED.
- [ ] Release tag `v1.6.0` exists.
- [ ] GitHub Release publication is verified.

Verification on 2026-09-12 (local Python 3.14): `.venv/bin/python -m pytest -q` → **153 passed in 39.39s**. This is local evidence, not a successful GitHub Actions Python 3.12 run. `git diff --check` passed; local Markdown links and JSON examples validated.

### Limits

- **AC-2:** The current integration evidence verifies state and output, not complete descendant termination or bounded return time.
- **AC-6:** Cancellation observed between successful global_setup and entry to setup also skips teardown. Unexpected Python exceptions are outside the current cleanup guarantee.
- **AC-8:** A pre-cancelled run can have zero cancelled steps. Consumers use `summary.status` rather than the limited `RunResult.passed` helper.

Related records: [Test matrix](../test_matrix/test_matrix_v1.6.0.md) · [Definition of done](../definition_of_done/definition_of_done_v1.6.0.md).

## Acceptance decision

cancellation foundation is documented within the observed implementation and test boundaries. Full release readiness remains pending for the unchecked items; no issue closure or release publication is inferred from this local update.
