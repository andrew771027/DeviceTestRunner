# GitHub Actions Coverage Configuration

## Current configuration

Coverage uses pytest-cov with configuration in [pyproject.toml](../../pyproject.toml). The measured package is `runner`. No pytest.ini or .coveragerc is required by the current repository.

| Setting | Value | Effect |
| --- | --- | --- |
| tool.coverage.run.source | `["runner"]` | Measure production runner code |
| tool.coverage.run.branch | true | Include branch coverage |
| tool.coverage.report.fail_under | 80 | Fail when combined coverage is below 80% |
| show_missing / skip_covered | true / false | Show missing lines and include fully covered files |
| HTML directory | artifacts/coverage/html | Local default for HTML output |
| XML output | artifacts/coverage/coverage.xml | Local default for XML output |

Pytest uses testpaths=tests, -ra, --strict-markers and --strict-config. Coverage is enabled by command-line arguments, not by default pytest addopts. pytest-cov is declared in both project dependencies and the dev dependency group; this document records the current declaration, not a dependency cleanup.

## Run locally

From the repository root:

```bash
poetry run pytest tests/test_unit \
  --cov=runner \
  --cov-report=term-missing \
  --cov-report=xml:artifacts/coverage/coverage.xml \
  --cov-report=html:artifacts/coverage/html
```

`make test_cov` runs verbose unit tests with `--cov=runner --cov-report=term-missing`. `make test` runs all tests without enabling coverage. Full-suite success alone does not prove the unit-only coverage threshold passes.

## CI job and artifacts

The coverage job in [ci.yml](../../.github/workflows/ci.yml) uses Ubuntu and Python 3.12, installs Poetry 2.x and runs `poetry install --no-interaction`. It creates the coverage directories and executes the unit-only command above.

The upload step runs with `if: always()`, uploads artifacts/coverage/ as coverage-python-3.12, retains it for 14 days and warns if files are missing. A failed test or threshold can still leave downloadable reports; upload success does not mean tests passed.

Other CI jobs run unit tests on Python 3.11, 3.12 and 3.13, and integration tests on Python 3.14. The integration artifact is currently named integration-python-3.12 despite that job's Python 3.14 setting; inspect workflow configuration when interpreting artifact names. Code Quality uses Python 3.14 and pre-commit.

## Quality gate integration

The `coverage` job is required by [PR Quality Gate](ci_pull_request_quality_gate.md).
A failed unit test or coverage below 80% fails this dependency and therefore the
gate when it executes. Uploading reports does not override that result.

## Verification boundary

This describes the checked-in workflow, not an observed remote run. Local full-suite and package checks for this documentation update are recorded in [v1.7.1 Definition of Done](../definition_of_done/definition_of_done_v1.7.1.md). The project/lock mismatch observed during documentation editing was resolved by regenerating poetry.lock; poetry check --lock now passes. Dependency installation and CI must be verified separately.
