# PyPI Trusted Publishing

## Overview

Device Test Runner publishes Python distributions to PyPI using GitHub Actions Trusted Publishing.

Trusted Publishing uses OpenID Connect (OIDC) to authenticate the GitHub Actions publishing workflow to PyPI.

No long-lived PyPI API token is stored in GitHub.

```text
GitHub Actions
      ↓
OIDC identity
      ↓
PyPI Trusted Publisher
      ↓
Short-lived publishing credential
      ↓
PyPI
```

## Release Architecture

The release process separates build and publishing responsibilities.

```text
Git Tag
   ↓
Build Job
   ↓
Tests
   ↓
Build Wheel + sdist
   ↓
Package Validation
   ↓
GitHub Actions Artifact
   │
   ├── GitHub Release
   │
   └── PyPI Publish Job
```

The package is built once and the same validated distribution files are promoted to each distribution channel.

## Distribution Files

The release build produces:

```text
dist/
├── devicetestrunner-<version>-py3-none-any.whl
└── devicetestrunner-<version>.tar.gz
```

The wheel is the built Python distribution.

The `.tar.gz` file is the source distribution.

## PyPI Trusted Publisher

The PyPI project configures a GitHub Actions Trusted Publisher using:

```text
GitHub owner
GitHub repository
Workflow filename
GitHub Environment
```

Example:

```text
Owner:
andrew771027

Repository:
DeviceTestRunner

Workflow:
release.yml

Environment:
pypi
```

The configured values must match the GitHub Actions workflow identity.

## GitHub Environment

The production publishing job uses the GitHub Environment:

```text
pypi
```

The environment should be protected with manual approval when appropriate.

The environment is used as part of the Trusted Publisher identity and as a deployment protection boundary.

No PyPI API token is stored in the environment.

## OIDC Permission

The publishing job requires:

```yaml
permissions:
  id-token: write
```

This allows GitHub Actions to obtain an OIDC identity token.

It does not grant general repository write access.

The publishing job should receive only the permissions it requires.

## Publishing Job

The publishing job downloads distributions produced by the build job.

```yaml
- name: Download package distributions
  uses: actions/download-artifact@v7
  with:
    name: python-package-distributions
    path: dist/
```

It then publishes the contents of `dist/` using:

```yaml
- name: Publish package to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
```

No username, password, or PyPI API token is configured.

## Build and Publish Separation

Distribution packages must be built in a separate job from the PyPI publishing job.

The build job performs:

```text
Checkout
Tests
Version validation
Package build
Metadata validation
Wheel smoke test
Artifact upload
```

The publishing job performs:

```text
Download validated distributions
Publish to PyPI
```

This minimizes the amount of code executed inside the OIDC-enabled publishing job.

## Build Once

Device Test Runner follows a build-once policy.

```text
Source
  ↓
Build
  ↓
Validated Wheel + sdist
  ↓
┌─────────────────┬─────────────────┐
│ GitHub Release  │ PyPI            │
└─────────────────┴─────────────────┘
```

The GitHub Release and PyPI publication use the same package artifacts.

The package should not be rebuilt independently for each distribution channel.

## Package Validation

Before a distribution is eligible for publication, the workflow validates package metadata:

```bash
twine check dist/*
```

The wheel is also installed into a clean Python virtual environment:

```bash
python -m venv /tmp/dtr-release-test

/tmp/dtr-release-test/bin/python \
  -m pip install dist/*.whl
```

A basic import or CLI smoke test should then be executed.

For example:

```bash
/tmp/dtr-release-test/bin/python \
  -c "import device_test_runner"
```

This validates the packaged distribution rather than only the source repository.

## Version Policy

Git tags and Python package versions must match.

Example:

```text
Git tag:
v1.7.4

Python package:
1.7.4
```

The release workflow must fail when these versions differ.

Published PyPI versions are treated as immutable.

If a released version contains a defect, create a new version rather than replacing an existing distribution.

```text
1.7.4
  ↓
fix
  ↓
1.7.5
```

## TestPyPI

TestPyPI may be used to validate the publishing workflow before publishing a production release.

TestPyPI should use a separate GitHub Environment:

```text
testpypi
```

and a separately configured TestPyPI Trusted Publisher.

Publishing to TestPyPI uses:

```yaml
- name: Publish package to TestPyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    repository-url: https://test.pypi.org/legacy/
```

PyPI and TestPyPI are separate package indexes.

## Security

The publishing workflow follows least privilege.

```text
CI jobs
→ contents: read

Build job
→ contents: read

GitHub Release job
→ contents: write

PyPI publishing job
→ id-token: write
```

The PyPI publishing job should not checkout or build source code unless there is a specific requirement.

Its responsibility should remain limited to publishing already validated distribution artifacts.

## Secrets

Trusted Publishing does not require:

```text
PYPI_TOKEN
PYPI_API_TOKEN
PYPI_PASSWORD
```

Long-lived PyPI credentials should not be added to the GitHub repository when Trusted Publishing is available.

## Workflow Protection

The trusted publishing workflow is part of the package security boundary.

Changes to:

```text
.github/workflows/release.yml
```

should go through the repository's normal Pull Request and Quality Gate process.

A dedicated release workflow should be used rather than granting publishing identity to a general CI workflow.

## Traceability

A production package should be traceable through:

```text
Git commit
    ↓
Git tag
    ↓
Build workflow
    ↓
Wheel / sdist
    ↓
GitHub Release
    ↓
PyPI project version
```

This provides a clear relationship between source code and the published Python distribution.