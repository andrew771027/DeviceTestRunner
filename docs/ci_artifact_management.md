# GitHub Actions Artifact Management

## Overview

Device Test Runner CI stores test evidence as GitHub Actions artifacts.

The CI pipeline preserves:

- pytest JUnit reports
- pytest logs
- selected Device Test Runner execution artifacts

## CI Artifact Flow

```text
                        GitHub Actions
                              │
          ┌───────────────────┼──────────────────┐
          ▼                   ▼                  ▼
      Code Quality        Unit Matrix       Integration
                              │                  │
                    ┌─────────┼────────┐         │
                    ▼         ▼        ▼         ▼
                  3.11      3.12     3.13     DTR v1.7
                    │         │        │         │
                    ▼         ▼        ▼         ▼
                  JUnit     JUnit    JUnit    JUnit
                  Logs      Logs     Logs     Logs
                                                 │
                                                 ▼
                                          report.json
                                          stdout/stderr
                                                 │
                 ┌───────────────────────────────┘
                 ▼
          GitHub Artifacts
```

## Artifact Structure

```text
artifacts/
├── unit/
│   ├── reports/
│   │   └── junit.xml
│   └── logs/
│       └── pytest.log
│
└── integration/
    ├── reports/
    │   └── junit.xml
    ├── logs/
    │   └── pytest.log
    └── dtr/
        ├── report.json
        ├── stdout.log
        └── stderr.log
```

## Unit Test Artifacts

Each supported Python version produces an independent artifact.

```text
unit-python-3.11
unit-python-3.12
unit-python-3.13
```

Each artifact contains:

- JUnit test result
- pytest log

## Integration Test Artifacts

Integration testing produces:

```text
integration-python-3.12
```

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

This allows diagnostic output to be preserved even when tests fail.

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
