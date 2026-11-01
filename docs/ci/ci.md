# Continuous Integration

## Overview

Device Test Runner uses GitHub Actions to automate code quality checks and testing.

The CI workflow runs on:

* Pushes to `main`
* Pull requests targeting `main`

Pushes to other branches do not trigger this workflow. There are no path filters,
so documentation-only pull requests targeting `main` also run CI.

## CI Pipeline

Validation jobs run independently and feed the aggregate gate:

```text
Code Quality ───────────────────────┐
Unit Tests (Python 3.11/3.12/3.13) ──┤
Coverage (Python 3.12) ──────────────┼── PR Quality Gate
Integration Tests (Python 3.14) ────┘
```

| Job ID | Validation |
| --- | --- |
| `code-quality` | pre-commit on Python 3.14 |
| `unit-tests` | Unit tests on Python 3.11, 3.12 and 3.13; `fail-fast: false` |
| `coverage` | Unit tests with runner coverage on Python 3.12; minimum 80% |
| `integration-tests` | Integration tests on Python 3.14 |
| `pr-quality-gate` | Require all four upstream jobs to report `success` |

Each validation job checks out the repository, sets up Python, installs Poetry
2.x and runs `poetry install --no-interaction`. Test and coverage jobs upload
artifacts with `if: always()`.

The aggregate gate uses `needs` and `if: always()` to evaluate upstream results
even after validation failures. It runs on both supported workflow events.
See [Pull Request Quality Gate](ci_pull_request_quality_gate.md) for repository
protection configuration and the current runner-label issue.

## Local Development

Code Quality and integration tests use Python 3.14. Unit compatibility testing
uses Python 3.11–3.13; coverage uses Python 3.12.
`.pre-commit-config.yaml` selects Python 3.14 for hook environments.
Poetry 2.x installs dependencies from `poetry.lock`, including pre-commit and pytest.

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

Configure `PR Quality Gate` as a required status check in the `main` ruleset to
enforce validation at merge time. The workflow does not configure repository
rules itself. When the gate executes, a failed, cancelled or skipped upstream
job causes it to fail.

`poetry check --lock` above is a local consistency check; the workflow does not
run it as a separate step.

## Scope

CI includes code quality checks, unit and integration testing, coverage reports,
and retained test artifacts. Deployment and hardware-dependent test execution
are outside the workflow's scope.

## Related Documentation

* [CI workflow](../../.github/workflows/ci.yml)
* [Pull Request Quality Gate](ci_pull_request_quality_gate.md)
* [Matrix testing](ci_matrix_testing.md)
* [Coverage configuration](ci_coverage.md)
* [Artifact management](ci_artifact_management.md)
