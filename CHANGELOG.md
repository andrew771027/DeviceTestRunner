# Changelog

## [Unreleased]

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
