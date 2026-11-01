# Pull Request Quality Gate

## Overview

Device Test Runner uses GitHub Actions to validate changes. When repository rules require `PR Quality Gate`, changes cannot be merged into `main` unless that check succeeds. The workflow does not create or enable repository rules.

The repository exposes a stable required check:

```text
PR Quality Gate
```

The quality gate aggregates the results of the internal CI jobs.

## Architecture

```text
Pull Request
     │
     ▼
GitHub Actions
     │
     ├── Code Quality
     ├── Unit Tests
     │    ├── Python 3.11
     │    ├── Python 3.12
     │    └── Python 3.13
     ├── Coverage
     └── Integration Tests
             │
             ▼
      PR Quality Gate
             │
       ┌─────┴─────┐
       ▼           ▼
     PASS          FAIL
       │             │
   Merge allowed   Merge blocked
```

## Aggregate Quality Gate

The final quality gate in [ci.yml](../../.github/workflows/ci.yml) depends on all
four validation jobs. The intended configuration is shown below.

The checked-in workflow currently spells the gate runner as `ununtu-latest`.
Correct it to `ubuntu-latest` before relying on the gate: the current label does
not select the intended GitHub-hosted Ubuntu runner.

```yaml
pr-quality-gate:
  name: PR Quality Gate
  runs-on: ubuntu-latest

  needs:
    - code-quality
    - unit-tests
    - coverage
    - integration-tests

  if: always()
```

`if: always()` ensures that the quality gate executes even when an upstream validation job fails.

The quality gate treats only `success` as an acceptable upstream result.

When the gate executes, failures, cancellations, or skipped required validation cause it to fail. `if: always()` does not guarantee completion if the workflow itself is cancelled or a runner is unavailable.

## Repository Rules

The `main` branch should be protected using a GitHub repository ruleset.

Recommended configuration:

```text
Require a pull request before merging
    enabled

Require status checks before merging
    enabled

Required check:
    PR Quality Gate

Require branches to be up to date before merging
    enabled

Force pushes
    disabled

Branch deletion
    disabled
```

Human review requirements may be added independently when appropriate.

## Stable Check Name

`PR Quality Gate` is treated as the stable CI interface exposed to repository protection.

Internal jobs may evolve without requiring the repository ruleset to track every implementation detail.

For example:

```text
Unit Tests
Coverage
Integration Tests
Security Scan
Packaging
```

may change over time while:

```text
PR Quality Gate
```

remains stable.

## Merge Policy

With the required-check ruleset enabled, all required validation must succeed before merging. A passing gate satisfies this check; other repository requirements may still block merging.

```text
Code Quality       PASS
Unit Tests         PASS
Coverage           PASS
Integration Tests  PASS

PR Quality Gate    PASS

Merge              ALLOWED
```

If any required validation fails:

```text
Coverage            FAIL
        ↓
PR Quality Gate     FAIL
        ↓
Merge               BLOCKED
```

## Required Check Design

Avoid making every internal matrix job a repository-level required check unless there is a specific reason.

Prefer:

```text
Ruleset
    ↓
PR Quality Gate
```

rather than coupling repository protection directly to every internal job and matrix configuration.

This keeps the merge policy stable while allowing the CI implementation to evolve.

## Workflow Filtering

The workflow runs on pushes to `main` and pull requests targeting `main`.
Pushes to other branches do not trigger it. There are no path filters.
Code Quality and Integration Tests use Python 3.14; Coverage uses Python 3.12.
Unit Tests use the Python 3.11/3.12/3.13 matrix. All matrix entries must succeed
for the `unit-tests` dependency to succeed.

Required workflows should not be configured in a way that causes them to disappear for normal pull requests.

Path filtering can cause a required workflow not to run, leaving the repository waiting for a status that is never reported.

The PR Quality Gate should therefore produce a result for every pull request targeting the protected branch.

## Coverage Policy

Coverage remains part of the quality gate.

The current minimum threshold is:

```text
80%
```

A coverage regression below this threshold causes the Coverage job to fail, which in turn fails the PR Quality Gate.

## Device Test Runner v1.7.2

The quality gate protects changes across the Device Test Runner execution model, including:

```text
Static variable substitution
Environment variable substitution
Runtime context
Runner lifecycle
Retry
Cancellation
Timeout handling
Artifact validation
Failure classification
```

The goal of the quality gate is not simply to make CI green.

Its purpose is to define the minimum automated evidence required before a change is accepted into the protected branch.

## Related Documentation

- [CI overview](ci.md)
- [Matrix testing](ci_matrix_testing.md)
- [Coverage configuration](ci_coverage.md)
- [Artifact management](ci_artifact_management.md)
