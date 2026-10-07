# Device Test Runner v1.6.3 Definition of Done

Version scope: Cancellation-Aware Cleanup. Source baseline: `f9337ec` plus the inspected working tree, compared with tag `v1.6.2`. Local Git history was inspected from the initial commit through this baseline; no v1.6.3 tag was found locally. Remote release state was not queried.

## Product and architecture

- [x] ConfigLoader accepts optional cleanup budget through the finite-positive timeout parser.
- [x] CleanupScope owns a fresh token and optional cleanup watchdog.
- [x] Cleanup stages, attempts and retry delays share that token and deadline.
- [x] Run watchdog stops before cleanup; final artifact validation runs afterward.
- [x] Successful global_setup determines teardown eligibility; global_teardown is attempted independently while cleanup remains active.
- [x] CleanupSummary is serialized and original run cancellation has priority over cleanup/artifact failure.
- [x] Runtime and project versions match 1.6.3; reports use DeviceTestRunner.VERSION.
- [x] Class and sequence Mermaid diagrams match inspected source flow.

## Quality and documentation

- [x] README, CHANGELOG, roadmap, cleanup guide and four v1.6.3 version documents describe source and tests.
- [x] Test guide includes token identity, real subprocess fixtures, bounded polling and docstring AST comparison.
- [x] Historical version documents and dated results retained.
- [x] All 196 test functions have one concrete Given/When/Then description.
- [x] Added descriptions to ten functions; their executable AST matched the initial staged test files before synchronizing four report-version assertions. Final AST comparison allows only that expected version change.
- [x] AI collaboration records distinguish product fixes, fixture fixes and provided partial CSV test.
- [x] Weak fixture assertions are documented rather than treated as complete guarantees.

## Local verification — 2026-10-07

Environment: Darwin x86_64, repository Python 3.14.0 `.venv`. This is local evidence, not Linux CI or release validation.

| Check | Command / method | Observed result |
| --- | --- | --- |
| Before documentation/version edits | `.venv/bin/python -m pytest -q` | 223 passed, 1 warning in 48.76s |
| After version declarations, before assertion synchronization | `.venv/bin/python -m pytest -q` | 7 failed, 216 passed, 1 warning in 50.00s; four assertions still expected 1.6.2 |
| Package version | `poetry version --short` | 1.6.3 |
| After report-version assertion synchronization | `.venv/bin/python -m pytest -q` | 223 passed, 1 warning in 49.59s |
| Documentation | Relative links, Markdown fences, JSON parsing and matrix references | 82 local links; examples and test names verified |
| After pytest.ini correction: full suite | `.venv/bin/python -m pytest -q` | 223 passed in 47.37s; no warnings |
| After pytest.ini correction: collection | `.venv/bin/python -m pytest --collect-only -q` | 223 tests collected in 0.17s; no warnings |
| Whitespace | `git diff --check` | Passed |
| Lock/configuration | `poetry check --lock` | All set! |
| Test descriptions | AST audit across tests | 196 functions; one Given/When/Then per function |
| Test behavior unchanged | Strip docstrings and compare AST with initial staged files | All three docstring-modified files matched before report-version synchronization |

The earlier runs emitted PytestConfigWarning because pytest.ini used TOML-style `testpaths = ["tests"]`. INI parsing produced the nonexistent `[tests]` path, triggering recursive discovery. The configuration now uses `testpaths = tests`; earlier warning results above remain historical evidence. Sample configuration was not executed during this documentation update.

Flake8 invocation was attempted with the five modified test files, but `.venv/bin/python -m flake8` could not run because flake8 is not installed in this environment. No lint pass is claimed.

## Release and follow-up

- [ ] Strengthen the dual-timeout fixture: scenario Bash command has an unmatched quote, so it does not reliably model a sleeping scenario.
- [ ] Strengthen cleanup skip evidence: touch -c on an absent marker cannot prove the second command never ran; assert launched steps or use a creating marker.
- [ ] Add shared deadline accumulation across multiple successful cleanup steps, cleanup retry-delay interruption and boundary race coverage.
- [ ] Add positive/null/full-YAML cleanup configuration coverage and direct status combinations for cleanup failure with cancellation reasons.
- [ ] Verify runtime report versions with a distribution installation; this update changes version declarations without reinstalling the package.
- [ ] Add exception-safe cleanup, artifact finalization and reporting for unexpected Python exceptions and second SIGINT.
- [ ] Return a nonzero CLI exit code for TIMED_OUT and add CLI integration coverage.
- [ ] Correct CancellationToken.cancel return annotation and define direct Python configuration validation guarantees.
- [ ] Verify Linux CI, detached descendants, normally exiting parents with surviving children and real CLI signals.
- [ ] Verify a passing sample configuration and GitHub issue/milestone state.
- [ ] Create or verify v1.6.3 tag and GitHub Release publication.

Release readiness: controlled cleanup is implemented and local tests pass, but unchecked evidence and release items remain open. No commit, push, tag or release was performed.


## User manual extraction — 2026-10-07

The full User Manual now lives in [docs/user_manual.md](../user_manual.md); README keeps a runnable quick start and links to the manual. Source-based tables cover YAML fields, required/optional values, defaults, usage and examples, plus validation types, environment variables, CLI and report interpretation. CommitManual defines this structure for future updates.

Documentation-only verification used repository Python 3.14.0 and temporary output directories. Both the README echo example and manual CSV example ran through ConfigLoader and the real runner: PASSED with result.json present. Eight YAML configurations/fragments loaded successfully (fragments merged with the complete starter configuration); Python examples parsed as AST and JSON examples parsed successfully. Thirty-two local links and Markdown fences were checked; git diff --check passed. No product or test behavior changed, and the full pytest suite was not rerun for this extraction; the earlier results remain above.
