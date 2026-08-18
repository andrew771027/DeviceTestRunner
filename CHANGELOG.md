# Changelog

## [Unreleased]

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
