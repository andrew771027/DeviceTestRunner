# Continuous Integration

## Overview

Device Test Runner uses GitHub Actions to automate code quality checks and testing.

The CI workflow runs on:

* Pushes to `main`
* Pull requests targeting `main`

## CI Pipeline

```text
Checkout
    ↓
Setup Python
    ↓
Install Dependencies
    ↓
Ruff Lint
    ↓
Ruff Format Check
    ↓
pytest
    ↓
Success / Failure
```

## Local Development

Install project dependencies:

```bash
poetry install
```

Run lint:

```bash
poetry run ruff check .
```

Check formatting:

```bash
poetry run ruff format --check .
```

Run tests:

```bash
poetry run pytest
```

## Fixing Code Quality Issues

Automatically fix supported lint violations:

```bash
poetry run ruff check --fix .
```

Format the codebase:

```bash
poetry run ruff format .
```

Review all changes before committing.

## Quality Gates

| Check       | Purpose                              |
| ----------- | ------------------------------------ |
| Ruff Lint   | Detect code quality issues           |
| Ruff Format | Enforce consistent formatting        |
| pytest      | Verify expected application behavior |

A failing check causes the CI job to fail. Subsequent steps are skipped by default.

## Scope

Version 0.2 focuses on Python code quality and existing automated tests.

Not included:

* Coverage reporting
* Test artifacts
* Matrix testing
* Deployment
* Hardware-dependent test execution

## Workflow

`.github/workflows/ci.yml`
