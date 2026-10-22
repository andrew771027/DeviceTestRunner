# GitHub Actions Matrix Testing

## Overview

Device Test Runner uses GitHub Actions matrix testing to verify unit tests against multiple supported Python versions.

Current matrix:

```text
Python 3.11
Python 3.12
Python 3.13
```

The same unit test suite is executed independently for each Python version.

## Architecture

```text
Unit Test Job
      │
      ├── Python 3.11
      │      └── pytest tests/test_unit
      │
      ├── Python 3.12
      │      └── pytest tests/test_unit
      │
      └── Python 3.13
             └── pytest tests/test_unit
```

## Workflow Configuration

```yaml
strategy:
  fail-fast: false

  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

The selected Python version is passed to `actions/setup-python`:

```yaml
- name: Setup Python ${{ matrix.python-version }}
  uses: actions/setup-python@v7
  with:
    python-version: ${{ matrix.python-version }}
```

## Why Matrix Testing?

Matrix testing helps verify that Device Test Runner behaves consistently across its supported Python runtime versions.

It can detect:

- Python-version incompatibilities
- Dependency incompatibilities
- Runtime-specific behavior changes
- Accidental use of newer Python-only features

## Local Development

Developers can continue running the normal unit test suite locally:

```bash
poetry run pytest tests/test_unit
```

GitHub Actions is responsible for executing the compatibility matrix.

## Current Scope

Version 0.4 applies matrix testing to unit tests only.

Integration tests continue to run using the project's primary Python version.

Future versions may introduce additional matrix dimensions such as operating system or environment configuration.
