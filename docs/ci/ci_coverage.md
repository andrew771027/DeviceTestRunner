# GitHub Actions Coverage Configuration

## Overview

Device Test Runner uses `pytest-cov` and `coverage.py` to measure test coverage and enforce a minimum coverage threshold.

Two configuration styles are supported:

```text
Option A
pyproject.toml

Option B
pytest.ini + .coveragerc
```

Both configurations should represent the same coverage policy.

---

## Option A — pyproject.toml

Coverage configuration can be stored directly in `pyproject.toml`.

```toml
[tool.coverage.run]
branch = true
source = ["device_test_runner"]

[tool.coverage.report]
show_missing = true
skip_covered = false
fail_under = 80

exclude_also = [
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]

[tool.coverage.html]
directory = "artifacts/coverage/html"

[tool.coverage.xml]
output = "artifacts/coverage/coverage.xml"
```

Run coverage:

```bash
poetry run pytest tests/test_unit \
  --cov=device_test_runner \
  --cov-report=term-missing \
  --cov-report=xml \
  --cov-report=html
```

The coverage threshold is defined by:

```toml
fail_under = 80
```

If total coverage falls below 80%, the test command returns a non-zero exit code and the CI coverage job fails.

---

## Option B — pytest.ini + .coveragerc

Coverage configuration can also be separated into pytest configuration and coverage configuration.

### pytest.ini

```ini
[pytest]
testpaths = tests

addopts =
    --cov=device_test_runner
    --cov-report=term-missing
    --cov-report=xml
    --cov-report=html
```

The pytest configuration controls how the test suite invokes `pytest-cov`.

With this configuration, developers can run:

```bash
poetry run pytest tests/test_unit
```

without repeating the coverage command-line arguments.

---

### .coveragerc

```ini
[run]
branch = True
source =
    device_test_runner

[report]
show_missing = True
skip_covered = False
fail_under = 80

exclude_also =
    if TYPE_CHECKING:
    if __name__ == .__main__.:

[html]
directory = artifacts/coverage/html

[xml]
output = artifacts/coverage/coverage.xml
```

The `.coveragerc` file controls coverage measurement and reporting policy.

Responsibilities include:

```text
branch coverage
source package
coverage threshold
excluded patterns
HTML output
XML output
```

---

## Configuration Responsibility

The recommended separation is:

```text
pytest.ini
    ↓
How pytest runs

.coveragerc
    ↓
How coverage is measured

GitHub Actions
    ↓
When coverage is executed
```

For example:

```yaml
- name: Run unit tests with coverage
  run: poetry run pytest tests/test_unit
```

The CI workflow does not need to duplicate the coverage policy.

---

## Coverage Threshold

The current minimum coverage requirement is:

```text
80%
```

The threshold should primarily act as a regression guard.

Coverage below the threshold causes the CI coverage job to fail.

Coverage percentage should not be treated as a direct measurement of test quality.

---

## Branch Coverage

Branch coverage is enabled:

```ini
[run]
branch = True
```

or:

```toml
[tool.coverage.run]
branch = true
```

Branch coverage is particularly useful for Device Test Runner because the implementation contains significant control-flow logic, including:

```text
Retry decisions
Cancellation
Timeout handling
Failure classification
Artifact validation
Variable substitution
Environment variable resolution
```

Testing both sides of important decision branches provides more useful information than line coverage alone.

---

## Coverage Reports

Three forms of coverage output are used.

### Terminal

```text
term-missing
```

Used for quick CI diagnostics and displays uncovered line numbers.

### XML

Output:

```text
artifacts/coverage/coverage.xml
```

Used as machine-readable coverage data for future CI integrations.

### HTML

Output:

```text
artifacts/coverage/html/
```

The main entry point is:

```text
artifacts/coverage/html/index.html
```

The HTML report is useful for inspecting covered and uncovered source lines.

---

## Exclusions

The coverage configuration may exclude code that is not meaningful to execute during normal tests.

Current examples:

```text
if TYPE_CHECKING:
if __name__ == "__main__":
```

Exclusions should be conservative.

Production code should not be excluded only to increase the reported coverage percentage.

---

## pyproject.toml vs pytest.ini

Both approaches are valid.

### pyproject.toml

Recommended when Python tooling configuration is centralized.

```text
pyproject.toml
├── Poetry
├── pytest
├── Ruff
└── Coverage
```

### pytest.ini + .coveragerc

Recommended when explicit separation of tool responsibilities is preferred.

```text
pytest.ini
    → pytest configuration

.coveragerc
    → coverage configuration
```

Device Test Runner may use either approach, but the repository should maintain one authoritative coverage policy to avoid configuration drift.