# Changelog

## [1.7.2]

Scope: device runtime context. Inspected source `940fe66`, tests `2aeb559` and guide draft `278e012`; release publication is unverified.

### Added

- `${{ device.serial }}`, `${{ device.product }}` and `${{ device.build }}` references in lifecycle commands and artifact validation paths.
- `StaticVariableResolver.bind_device()` validates and copies resolved identity once per resolver, before run directory allocation; repeated binding and unknown device fields raise VariableResolutionError.
- Runtime-context unit tests and real subprocess integration cases; current usage guides and v1.7.2 architecture, matrix, acceptance and completion records.

### Compatibility and limits

All three device fields must now be non-empty resolved strings, including configurations without templates. Product/build remain literal inputs; templates in them fail binding. Empty env values remain valid lookups but fail when used as serial. Context values are strings and cannot serve as numeric step timeouts. No device discovery, context.* namespace, step outputs, environment mapping, shell escaping or report schema change. Package/runtime version is 1.7.2. See [verification record](docs/definition_of_done/definition_of_done_v1.7.2.md).

## [1.7.1]

Scope: host environment references. Inspected baseline `c1d457c`; no release publication claimed.

### Added

- `${{ env.NAME }}` resolves strings from one host environment snapshot per run.
- device.serial supports template resolution before artifact run directory allocation; resolved identity appears in report metadata.
- Unit and integration cases cover missing/empty names, invalid syntax, snapshot stability, timeout type rejection and real YAML-to-report execution.
- v1.7.1 architecture, test matrix, acceptance and completion records; environment guide with a device-free example.
- CI unit coverage job on Python 3.12, branch coverage and 80% threshold, configured in pyproject.toml with pytest options and pytest-cov dependency; Makefile test_cov runs unit coverage. This describes configuration, not an observed CI pass.

### Fixed

- Resolver snapshot construction/import, env lookup and early serial/run-directory resolution errors documented in the source-fix commits.
- Current documentation links follow the variables/ and ci/ directory moves; environment test commands use actual test paths.
- Package/runtime/report expectations identify 1.7.1; nine environment tests now have Given/When/Then descriptions.

### Limits and verification

Env values are strings; no numeric timeout conversion, run/step environment mapping, defaults, escaping or secret masking. Serial errors precede allocation; later template errors may leave a directory without a report. Executor environments are copied separately from live os.environ. See [v1.7.1 completion record](docs/definition_of_done/definition_of_done_v1.7.1.md) for actual commands, lock consistency verification and open checks.

## [1.7.0]

Version scope: Static Variable Substitution. Package, runtime and report versions are synchronized to 1.7.0. This records the inspected working tree, not a published release.

### Added

- Optional YAML `variables` mapping with string, integer, float and boolean values.
- `${{ vars.NAME }}` and absolute `${{ run.dir }}` references in lifecycle commands, step timeouts and artifact validation paths.
- StaticVariableResolver validates definitions at load time and resolves immutable configuration copies after run directory creation, before watchdogs or subprocesses start.
- Standalone CSV example in `configs/advance_sample.yaml`; lifecycle/retry demonstration in `configs/basic_sample.yaml`.
- Resolver unit tests, real subprocess/artifact/report integration tests, and v1.7.0 architecture, test matrix, acceptance criteria and completion records.

### Changed

- Whole references preserve scalar types; embedded references render strings.
- Step timeouts accept finite positive integers and floats, rejecting booleans, numeric strings, zero, negatives, NaN and infinity.
- Runtime version and four report-version regression assertions match the package version.
- User manual, README, roadmap and test guide describe the supported substitution fields and fail-fast behavior.

### Fixed

- Timeout validation accepts positive integers instead of rejecting them and checks type before comparing unsupported values.
- Integration command templates use ordinary strings to preserve double braces, separate script arguments with whitespace, and parse report text with json.loads.

### Verification and limitations

- Commands and observed results: [v1.7.0 Definition of Done](docs/definition_of_done/definition_of_done_v1.7.0.md).
- Recursive references, literal escaping, arithmetic, environment/secret templates and arbitrary field substitution are unsupported.
- Resolution errors can leave an empty run directory and propagate without a JSON report. Substitution does not escape shell arguments.
- Existing CLI TIMED_OUT exit-code, exception-finalization and platform limitations remain; release checks are pending.

## [1.6.3]

Version scope: Cancellation-Aware Cleanup. Distribution, runtime and report versions are synchronized to 1.6.3. This entry describes the inspected working tree, not a verified release.

### Added

- Optional finite positive `cleanup_timeout_seconds`; missing/null leaves cleanup without an overall deadline.
- CleanupScope with a separate token shared by teardown, global_teardown, attempts and retry delays.
- CleanupTimeoutWatchdog and a shared CancellationWatchdog base for run and cleanup deadlines.
- Required `RunResult.cleanup_summary` with attempted, timed_out, failed and cancellation_reason; JSON reports preserve it alongside the original run reason.
- Cleanup parser, watchdog, token identity, real subprocess timeout, partial CSV and missing artifact regression cases.
- v1.6.3 architecture with Mermaid UML, test matrix, acceptance criteria, completion checklist and testing-guide cases.

### Changed

- Run watchdog stops before cleanup; final artifact validation runs after the cleanup scope.
- Cleanup failure produces FAILED unless original run cancellation selects TIMED_OUT or CANCELLED.
- Successful global_setup establishes teardown eligibility even if cancellation prevents setup from starting.
- README and roadmap describe the current cleanup configuration and reporting behavior.
- Full usage instructions live in docs/user_manual.md with source-based field tables, validation types, paths, CLI and report guidance; README keeps a short quick start.
- CommitManual defines the manual structure and field-reference checks for future versions.

### Fixed

- Corrected pytest.ini testpaths to INI syntax (`testpaths = tests`), avoiding the missing-testpaths warning and recursive-discovery fallback.
- Global teardown no longer depends on successful global setup; pre-cancelled runs and failed global setup still attempt final cleanup.
- Cleanup deadline skip path no longer reads an unassigned global_teardown_success variable.
- Four report-version assertions now expect 1.6.3, matching runtime metadata.
- Cleanup timeout test uses `bash -c 'sleep 60'` so it waits for cancellation rather than immediately failing to find a script.

### Verification and limitations

- Local commands, results and release gaps: [v1.6.3 Definition of Done](docs/definition_of_done/definition_of_done_v1.6.3.md).
- Two fixture weaknesses limit deadline/skip evidence; see the test matrix. Exception-safe finalization, Linux checks and CLI TIMED_OUT exit code remain open.
- cleanup_timeout_seconds is not serialized in metadata. RunResult construction requires cleanup_summary.
- No v1.6.3 tag was found locally; GitHub Release, issues and milestones were not verified.

## [1.6.2]

Version scope: Run-level Timeout. Distribution, runtime and report versions are synchronized to 1.6.2. This entry describes the working tree, not a verified release.

### Added

- Optional top-level `run_timeout_seconds`, validated as a finite positive number; omitted/null means unlimited run time.
- Monotonic watchdog shared across normal steps and retries; cancellation reasons preserve the first request.
- `TIMED_OUT` run status and metadata `cancel_reason`, `run_timeout_seconds`, `run_timed_out`.
- Configuration, cancellation reason, watchdog, status, setup timeout, retry delay, serialized attempt history and orphan process regression tests.
- v1.6.2 architecture, test matrix, acceptance criteria, completion checklist and testing-guide cases.

### Changed

- Consolidated README, lifecycle documentation, testing guidance and release checks for v1.6.2.

- `RunResult.passed` follows summary status; `StepAttemptResult.passed` is removed in favor of `success`.
- Run timeout interrupts normal work without retrying cancelled attempts; reachable cleanup uses fresh tokens and final validation still runs.

### Fixed

- Standardized run timeout report metadata on `run_timed_out`, with explicit JSON regression assertions.

- Omitted timeout returns None; watchdog uses Event.wait instead of the misspelled method.
- Terminator checks the original process group even after the direct child is reaped.
- Missing existence-rule targets report ARTIFACT_MISSING; size diagnostics no longer contain indentation spaces.
- Tests correct empty-directory classification, fixture paths, imports, report access and unordered status parameters.

### Verification and limitations

- Current commands and results: [v1.6.2 Definition of Done](docs/definition_of_done/definition_of_done_v1.6.2.md).
- CLI TIMED_OUT currently returns 0; cleanup has no independent total deadline. Exception finalization, platform checks and detached-process handling remain open.
- Package version is synchronized; tag and GitHub Release remain pending.

## [1.6.1]

Version scope: Safe Process Termination. Runtime is 1.6.1; distribution remains 1.6.0. This entry describes source changes, not a verified release.

### Added

- ProcessTerminator sends SIGTERM to an attempt process group, then SIGKILL after the grace period when needed.
- First SIGINT requests cancellation; the second raises KeyboardInterrupt. CLI run results use exit codes 0, 1 and 130.
- Real parent/child/grandchild tests cover timeout, cancellation, ignored SIGTERM, reader completion and saved stdout/stderr.
- Retry fixtures verify previous parent and child PIDs are absent when attempt two starts.
- Dedicated SIGINT handler tests and v1.6.1 architecture, test matrix, acceptance criteria and definition of done.

### Changed

- Executor starts a separate session for each attempt and requires an injected ProcessTerminator.
- Each output reader join has a two-second limit; cleanup failures can report PROCESS_ERROR or propagate if recovery also fails.
- Runtime and report metadata identify 1.6.1; result schema is unchanged from 1.6.0.
- Added Given/When/Then docstrings to 12 tests without changing their executable AST.

### Fixed

- Cleanup waits for the process group rather than treating parent exit as proof that descendants stopped.
- PermissionError during group probing no longer aborts the wait immediately.
- Retry tests use the correct fixture path, command quoting, lifecycle type, integer counter and artifact directory field.
- Executor timeout tests model the injected terminator; runner test log paths serialize as strings.

### Verification and limitations

- Local evidence and exact commands are recorded in [v1.6.1 Definition of Done](docs/definition_of_done/definition_of_done_v1.6.1.md).
- Detached descendants, normal completion with surviving children, Linux CI and end-to-end CLI signals remain unverified. SIGTERM is not wired to cancellation.
- Package version synchronization, tag, issue/milestone status and GitHub Release publication remain pending.

## [1.6.0]

Version scope: Cancellation Foundation. Runtime implementation is present; release tag and publication are not verified.

### Added

- Thread-safe `CancellationToken` with idempotent cancellation and `CancellationRequested` helper
- Optional cancellation token on `DeviceTestRunner.run` and required token input on `SubprocessExecutor.execute`
- `FailureType.CANCELLED`, attempt `timed_out`/`cancelled`, step `cancelled`, metadata `cancel_requested`, and summary `cancelled_steps`
- Token, cancellation routing, retry-delay interruption, report and real subprocess cancellation coverage
- Versioned architecture, test matrix, acceptance criteria and definition of done for v1.6.0

### Changed

- Executor polls completion, cancellation and timeout; direct-process termination waits two seconds before kill fallback
- Cancelled attempts skip attempt validation and retry; final validation still evaluates all rules
- Normal retry delays poll for cancellation; reachable cleanup uses fresh execution tokens
- CANCELLED takes precedence over failure status; cancelled steps are excluded from failed_steps
- YAML rejects `cancelled` in retry_on, and policy never retries cancellation even when Python configuration includes it
- Runtime/report and distribution versions are synchronized to `1.6.0`
- Audited all 150 test-function docstrings, adding or correcting 121 descriptions without changing executable test code

### Fixed

- Poetry explicitly includes the `runner` package, fixing wheel discovery for distribution name `devicetestrunner`
- Manual documentation workflow removes conflicting sandbox flags and maps its API-key secret to `CODEX_API_KEY` for the CLI invocation

### Verification and limitations

- Local Python 3.14: `.venv/bin/python -m pytest -q` — **153 passed in 39.39s**, observed 2026-09-12
- Sample configuration with only its output directory redirected to a temporary location returned FAILED: one failed step, one skipped step and five failed required artifact rules
- Full process-tree termination, bounded output-reader shutdown, CLI signal handling and exception-safe finalization remain unimplemented or unverified

## [1.5.3]

### Added

- Selective retry configuration through `retry.retry_on`, supporting `timeout`, `device_offline`, `process_error`, `artifact_missing`, and `artifact_invalid`
- Required／optional artifact semantics through the validation rule `required` field, which defaults to `true`
- `required` metadata on artifact validation results and `failed_required_artifact_rules` in the execution summary
- Retry cleanup safety coverage for optional artifacts, missing targets, relative paths, and paths outside the run directory
- Unit and integration coverage for configured and unconfigured failure types, artifact criticality, cleanup boundaries, and v1.5.3 report metadata

### Changed

- Retry is now allowed only when the attempt failure type is explicitly listed in `retry.retry_on` and attempt capacity remains
- YAML configurations that omit `retry_on` default to no retry; duplicate values are removed while preserving order, and unknown values or `none` are rejected
- Optional artifact failures remain visible in validation results but do not fail the step or final run and do not trigger retry
- Required artifact failures continue to affect attempt and run status, but only trigger retry when their failure type is configured
- Retry cleanup removes only required validation targets resolved inside the current run directory
- Runner and generated report metadata now identify version `1.5.3`
- Full test suite expanded to 134 Given／When／Then-described tests

### Removed

- Artifact-level `retry_on_failure`; retry eligibility is now controlled centrally by `retry.retry_on`, while artifact criticality is controlled by `required`

## [1.5.2]

### Added

- Unified `FailureType` categories for timeout, device offline, process error, missing artifact, and invalid artifact
- `FailureClassifier` for process and artifact outcomes
- Per-attempt failure classification in `StepAttemptResult` and `result.json`
- Unit and integration coverage for failure priority and real subprocess classification
- Given／When／Then descriptions for every test case

### Changed

- Retry decisions now use failure type instead of a success boolean
- Process failures take priority over artifact failures; missing artifacts take priority over invalid artifacts
- Test lifecycle cleanup guarantees were strengthened: `teardown` now runs after `setup` has started even when `setup` fails, while `global_teardown` always runs even when `global_setup` fails
- Main lifecycle stages still fail fast: a failed `global_setup` skips `setup`, `scenario`, and `teardown`; a failed `setup` skips `scenario`; cleanup stages continue through all configured steps
- Executor, validator, runner, retry policy, and report metadata identify the v1.5.2 failure-classification contract

## [1.5.1]

### Added

- Artifact-aware retry rules with `after_step` and `retry_on_failure`
- Per-attempt artifact validation results in `StepAttemptResult` and `result.json`
- Unit and integration coverage for retryable, non-retryable, and exhausted artifact validation failures

### Changed

- A step attempt now succeeds only when both the command and its retry-enabled artifact rules pass
- Artifact retry rules are filtered by their associated step; rules without retry opt-in remain part of final validation only
- Runner and generated report metadata now identify version `1.5.1`

## [1.5.0]

### Added

- Configurable retry policy with maximum attempts and retry delay
- Attempt tracking for step execution results
- Per-attempt stdout and stderr artifact logs
- Retry configuration validation and backward-compatible defaults

### Changed

- Runner now retries failed steps according to the configured policy
- Step results and console output now include attempt information

## [1.4.1]

### Added

- CSV content validation
- JSON content and expected-value validation

### Changed

- Improved artifact validation integration and reporting
- Expanded validation, configuration, and integration test coverage

## [1.4.0]

### Added

- Artifact validation pipeline
- File existence, minimum file size, and file extension validation rules
- Validation result aggregation in execution reports

### Changed

- Validation failures now affect the final run status

## [1.3.5]

### Added

- Real-time command output streaming to the console and artifact logs

### Changed

- Synchronized stdout and stderr handling across executor, runner, and artifacts

## [1.3.0]

### Added

- Test lifecycle orchestration
- Step result aggregation

### Changed

- Runner now manages lifecycle status

## [1.2.0]

### Added

- ArtifactManager
- report.json metadata

### Changed

- Moved report ownership from JsonReporter to ArtifactManager

## [1.1.0]

### Changed

- Renamed test models to avoid pytest collection warnings
- Aligned YAML and Python model naming

## [1.0.0]

### Added

- YAML scenario configuration
- Config loader
- Command step executor
- Basic DeviceTestRunner
