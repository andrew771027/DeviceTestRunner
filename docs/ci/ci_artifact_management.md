# GitHub Actions Artifact Management

## Overview

Device Test Runner CI stores test evidence as GitHub Actions artifacts.

The CI pipeline preserves:

- pytest JUnit reports
- pytest logs
- selected Device Test Runner execution artifacts

## CI Artifact Flow

Unit matrix entries, Coverage and Integration Tests upload separate artifacts.
Code Quality and PR Quality Gate do not produce report artifacts.

## Artifact Structure

Paths below are relative to the repository root before upload. Each upload uses
its job-specific directory as the artifact root.

```text
artifacts/
├── unit/
│   ├── results.xml
│   └── pytest.log
├── coverage/
│   ├── coverage.xml
│   └── html/
└── integration/
    ├── junit.xml
    ├── pytest.log
    ├── reports/
    ├── logs/
    └── dtr/
```

The integration job creates `reports/` and `logs/`, but pytest writes its report
and log directly under `artifacts/integration/`. `DTR_TEST_ARTIFACT_DIR` selects
`dtr/`; its contents depend on the tests.

## Unit Test Artifacts

Each supported Python version produces an independent artifact.

```text
unit-test-results-3.11
unit-test-results-3.12
unit-test-results-3.13
```

Each artifact contains:

- JUnit test result
- pytest log

## Coverage Artifacts

`coverage-python-3.12` contains `coverage.xml` and the `html/` report directory.
See [Coverage configuration](ci_coverage.md) for scope and threshold.

## Integration Test Artifacts

Integration testing produces:

```text
integration-python-3.12
```

The job runs on Python 3.14 despite the artifact's `3.12` suffix. The name above
matches the current workflow rather than the actual runtime version.

The artifact may contain:

- JUnit test result
- pytest log
- Device Test Runner reports
- selected subprocess stdout and stderr

## Failure Handling

Artifact upload uses:

```yaml
if: always()
```

This preserves existing diagnostic output even when tests fail. Unit uploads
use `if-no-files-found: error`; coverage and integration uploads use `warn`.
Uploads cannot preserve files that were never produced.

[PR Quality Gate](ci_pull_request_quality_gate.md) evaluates job results, not
artifact presence. A successful upload does not override a failed test.

## Retention

Normal CI artifacts are retained for a limited period.

Current policy:

```text
14 days
```

Long-term validation evidence should use dedicated persistent storage rather than normal CI artifacts.

## Security

Artifacts must not contain:

- secrets
- access tokens
- credentials
- private keys
- sensitive environment dumps

Only explicitly selected artifact directories should be uploaded.

## Artifact Policy

Unit tests store lightweight structured results and logs.

Integration tests may additionally store Device Test Runner execution evidence when useful for debugging.

Large or hardware-specific artifacts should be collected selectively.
