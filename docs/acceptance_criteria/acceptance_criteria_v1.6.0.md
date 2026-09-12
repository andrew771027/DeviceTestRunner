# Device Test Runner v1.6.0 Acceptance Criteria

Release theme: Cancellation Foundation

## AC-1 — Cancellation token

**Given** a new token shared with the runner
**When** a caller requests cancellation, including repeated requests
**Then** the token stays cancelled; `raise_if_cancelled()` raises `CancellationRequested`, while it does nothing on an active token.

## AC-2 — Cancel a running command

**Given** a command is still running with an active token
**When** the executor observes cancellation during polling
**Then** it stops the direct process, preserves captured output and returns `cancelled=true`, `timed_out=false`, `failure_type=cancelled`.

The current integration evidence verifies state and output, not complete descendant termination or bounded return time.

## AC-3 — Distinguish timeout

**Given** a command remains running beyond `timeout_second` without cancellation
**When** the executor observes timeout
**Then** it reports `timed_out=true`, `cancelled=false` and `failure_type=timeout`.

## AC-4 — Never retry cancellation

**Given** cancellation is reported with attempt capacity remaining
**When** runner or retry policy evaluates another attempt
**Then** no retry occurs; YAML `retry_on` rejects `cancelled`, and direct Python policy also refuses it even if explicitly listed.

## AC-5 — Interrupt retry delay

**Given** a failed normal step is waiting before retry
**When** its token becomes cancelled
**Then** polling ends the delay, no next attempt starts, and the step is marked cancelled while prior attempt evidence remains unchanged.

## AC-6 — Cleanup routing

**Given** cancellation occurs before run, during global_setup, or after entering setup/scenario
**When** the runner routes the remaining controlled lifecycle
**Then** pre-run/global_setup cancellation reaches global_teardown only, while setup/scenario cancellation reaches both cleanup stages; cleanup receives a fresh active execution token.

Cancellation observed between successful global_setup and entry to setup also skips teardown. Unexpected Python exceptions are outside the current cleanup guarantee.

## AC-7 — Artifact finalization

**Given** a cancelled attempt has required artifact rules
**When** the runner finalizes the run
**Then** attempt-level validation is skipped, all rules are still evaluated at run end, and required artifact failure does not override CANCELLED status.

## AC-8 — Report and status

**Given** cancellation was requested or a step was marked cancelled
**When** the runner writes `result.json`
**Then** metadata reports runtime `1.6.0` and `cancel_requested`, attempts expose cancellation/timeout flags, summary separates `cancelled_steps` from `failed_steps`, and final status is CANCELLED.

A pre-cancelled run can have zero cancelled steps. Consumers use `summary.status` rather than the limited `RunResult.passed` helper.

## Release Evidence

- [x] Unit and integration evidence maps to AC-1 through AC-8; boundaries are recorded in the Test Matrix.
- [x] All 150 test functions have reviewed Given／When／Then descriptions; executable test AST is unchanged.
- [x] Runtime source version is `1.6.0`.
- [x] README, Architecture, Test Matrix, Acceptance Criteria, Definition of Done, Roadmap and CHANGELOG are updated.
- [x] Distribution version in `pyproject.toml` is synchronized to `1.6.0`.
- [ ] Sample configuration completes with PASSED.
- [ ] Release tag `v1.6.0` exists.
- [ ] GitHub Release publication is verified.

Verification on 2026-09-12 (local Python 3.14): `.venv/bin/python -m pytest -q` → **153 passed in 39.39s**. This is local evidence, not a successful GitHub Actions Python 3.12 run. `git diff --check` passed; local Markdown links and JSON examples validated.

Acceptance decision: cancellation foundation is documented within the observed implementation and test boundaries. Full release readiness remains pending for the unchecked items; no issue closure or release publication is inferred from this local update.
