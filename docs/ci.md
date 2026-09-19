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
Install Poetry and Check Lock File
    ↓
Install Dependencies
    ↓
Pre-commit Hooks
    ↓
pytest
    ↓
Success / Failure
```

## Local Development

The workflow uses Ubuntu and Python 3.14, matching the Python version in
`.pre-commit-config.yaml`. Poetry 2.x installs dependencies from `poetry.lock`,
including pre-commit and pytest.

Check that project metadata and the lock file are consistent:

```bash
poetry check --lock
```

Install project dependencies:

```bash
poetry install
```

Run all code quality checks:

```bash
poetry run pre-commit run --all-files --show-diff-on-failure
```

Run tests:

```bash
poetry run pytest
```

## Fixing Code Quality Issues

Run the hooks locally to apply supported whitespace, import sorting, and
formatting fixes:

```bash
poetry run pre-commit run --all-files
```

Review all changes and rerun the command before committing. Hooks are configured
in `.pre-commit-config.yaml` and include pre-commit-hooks, isort, Black, and Flake8.
The first run downloads the hook environments and requires network access.

## Alternative Tool: Ruff

Ruff is an alternative for Python linting, import sorting, and formatting.
It is not currently installed by the project or used in CI. To try it as a
development dependency:

```bash
poetry add --group dev ruff
```

This updates `pyproject.toml` and `poetry.lock`. Run lint and formatting checks:

```bash
poetry run ruff check .
poetry run ruff check --select I .
poetry run ruff format --check --line-length 100 .
```

Apply supported fixes and formatting:

```bash
poetry run ruff check --fix .
poetry run ruff check --select I --fix .
poetry run ruff format --line-length 100 .
```

The line length matches the current formatting hooks. Ruff's default lint rules
and formatting are not identical to the existing Flake8, isort, and Black
configuration, and it does not replace all file hygiene checks in pre-commit.
Review any fixes and continue running the existing pre-commit checks before
committing. Adopting Ruff in CI would require updating the hook configuration
and agreeing on the lint rules first.

## Quality Gates

| Check       | Purpose                              |
| ----------- | ------------------------------------ |
| Poetry lock | Verify dependency metadata consistency |
| Pre-commit  | Check syntax, file hygiene, imports, formatting, and lint |
| pytest      | Verify expected application behavior |

A failing check causes the CI job to fail. Subsequent steps are skipped by default.

## Scope

CI checks code quality and runs the full unit and integration test suite with
`poetry run pytest`, including process cleanup, retry, and cancellation tests.

Not included:

* Coverage reporting
* Test artifacts
* Matrix testing
* Deployment
* Hardware-dependent test execution

## Workflow

[CI workflow](../.github/workflows/ci.yml)
