# Device Test Runner v1.6.1 Definition of Done

Version scope: Safe Process Termination. Source baseline: `0dbdc51`, compared with Git tag `v1.6.0`.

## Product and architecture

- [x] Attempts start in separate sessions; timeout and cancellation delegate to ProcessTerminator.
- [x] SIGTERM grace period checks the group; surviving members receive SIGKILL.
- [x] Each stdout/stderr reader has a bounded join and raises if still alive.
- [x] Real retry checks previous parent and child PIDs before the next attempt does work.
- [x] First SIGINT cancels the token; second handler invocation raises KeyboardInterrupt.
- [x] Runtime/report version is `1.6.1`; v1.6.0 result fields are preserved.
- [x] POSIX, early-exit, detached-process and exception-finalization limits are documented.

## Quality and documentation

- [x] Unit and integration coverage is mapped in the Test Matrix.
- [x] All 162 test functions have Given/When/Then docstrings; parametrization produces 168 cases.
- [x] This documentation update adds 12 missing descriptions; AST comparison confirms executable tests are unchanged.
- [x] README, CHANGELOG, Roadmap, Process Lifecycle and four v1.6.1 documents reflect source behavior.
- [x] Architecture contains Mermaid class and sequence diagrams.
- [x] Older versioned documents and their historical verification records are preserved.

### Local verification — 2026-09-17

Environment: macOS (`Darwin x86_64`), Python 3.14.0, repository `.venv`. This is local evidence, not proof of a successful Ubuntu/Python 3.12 CI run.

| Check | Command / method | Observed result |
| --- | --- | --- |
| Before documentation edits | `.venv/bin/python -m pytest -q` | 168 passed in 38.12s |
| After documentation edits | `.venv/bin/python -m pytest -q` | 168 passed in 38.46s |
| Test descriptions | AST docstring audit and workflow-style Given/When/Then line counts | 162 functions; 162 Given, 162 When, 162 Then |
| Test behavior | Compare AST with docstrings removed before/after editing | Unchanged for all test files |
| Documentation | Local relative links, JSON example parsing and Python example compilation | 8 documents, 28 links checked; examples parse/compile |
| Whitespace | `git diff --check` | Passed |

The sample configuration was not rerun during this documentation update. Its prior failure record remains in the [v1.6.0 Definition of Done](definition_of_done_v1.6.0.md); it is not current-version passing evidence.

## Release and follow-up

- [ ] Synchronize `pyproject.toml` distribution version (`1.6.0`) with runtime (`1.6.1`). This documentation task did not change package metadata.
- [ ] Verify a passing sample configuration.
- [ ] Verify Ubuntu CI and platform-specific process/zombie cleanup behavior.
- [ ] Add end-to-end CLI signal, exit-code and handler-restoration evidence.
- [ ] Define handling for detached descendants and normal completion with surviving background children.
- [ ] Verify cleanup/report finalization on unexpected exceptions or second Ctrl+C.
- [ ] Verify related GitHub issues and milestone completion.
- [ ] Create or verify tag `v1.6.1`; absent from inspected local tag refs on this update.
- [ ] Verify GitHub Release publication; not checked through a remote service.

Release readiness: the documented process-group behavior is implemented and locally tested. The unchecked release and boundary items remain open; no commit, push, tag or release was performed by this update.
