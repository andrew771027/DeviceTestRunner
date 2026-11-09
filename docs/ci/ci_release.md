# GitHub Actions Release Pipeline

## Overview

Device Test Runner uses a tag-driven GitHub Actions release workflow.

A release represents a specific, validated Device Test Runner source revision and its distributable Python packages.

The release process is separated from normal CI.

```text
Pull Request
    ↓
PR Quality Gate
    ↓
main
    ↓
Git Tag
    ↓
Release Workflow
    ↓
Build
    ↓
Package Validation
    ↓
GitHub Release
```

## Versioning

Device Test Runner follows version tags in the form:

```text
vMAJOR.MINOR.PATCH
```

Example:

```text
v1.7.3
```

The Git tag version must match the Python package version.

```text
Git tag:
v1.7.3

Package version:
1.7.3
```

A mismatch causes the release workflow to fail.

## Creating a Release

Update the local main branch:

```bash
git switch main
git pull origin main
```

Create an annotated tag:

```bash
git tag -a v1.7.3 -m "Device Test Runner v1.7.3"
```

Inspect the tag:

```bash
git show v1.7.3
```

Push the tag:

```bash
git push origin v1.7.3
```

Pushing the tag triggers the release workflow.

## Release Workflow Trigger

```yaml
on:
  push:
    tags:
      - "v*.*.*"
```

Normal pushes to `main` do not create releases.

## Release Validation

Before building a package, the release workflow verifies:

```text
Tagged commit belongs to main
Tag matches package version
Automated tests pass
```

The tagged commit must already be part of the protected `main` branch.

This preserves the relationship between the PR Quality Gate and the release process.

## Package Build

The package is built using Poetry:

```bash
poetry build
```

Expected output:

```text
dist/
├── device_test_runner-<version>-py3-none-any.whl
└── device_test_runner-<version>.tar.gz
```

The wheel is the built Python distribution.

The `.tar.gz` file is the source distribution.

## Package Smoke Test

The built wheel is installed into a clean virtual environment.

```bash
python -m venv /tmp/dtr-release-test

/tmp/dtr-release-test/bin/python \
  -m pip install dist/*.whl
```

This validates the built package rather than only validating the repository source tree.

When a CLI entry point is available, the release workflow should additionally execute a basic command such as:

```bash
dtr --help
```

## Package Artifact

Built packages are stored as GitHub Actions artifacts for build traceability.

Example:

```text
device-test-runner-v1.7.3
```

Contents:

```text
device_test_runner-1.7.3-py3-none-any.whl
device_test_runner-1.7.3.tar.gz
```

Workflow artifacts are temporary CI artifacts and are not treated as the primary release distribution channel.

## GitHub Release

The same built package files are attached to the GitHub Release.

The release is created using the existing Git tag.

```bash
gh release create v1.7.3 \
  dist/*.whl \
  dist/*.tar.gz \
  --verify-tag \
  --generate-notes
```

The release workflow must not silently create an unexpected tag.

## Permissions

Normal CI should use read-only repository permissions whenever possible.

```yaml
permissions:
  contents: read
```

The release workflow requires:

```yaml
permissions:
  contents: write
```

because it creates a GitHub Release.

Write permission should be limited to the release workflow.

## Release Immutability

A released version should not be rebuilt from a different commit under the same version number.

Do not move or recreate an existing release tag after publication.

If a released version requires a fix, create a new version.

Example:

```text
v1.7.3
    ↓
bug discovered
    ↓
v1.7.4
```

This preserves release traceability and reproducibility.

## Traceability

Every released package should have a clear source chain:

```text
Git commit
    ↓
Git tag
    ↓
GitHub Release
    ↓
Wheel / source distribution
```

For Device Test Runner, this allows a deployed runner version to be traced back to the exact source revision that produced it.

## Release Best Practices

The release process follows these principles:

- Release only from explicit version tags.
- Require released commits to belong to `main`.
- Match the Git tag and Python package version.
- Keep CI read-only and grant write access only to release jobs.
- Validate the release source before packaging.
- Test the built wheel in a clean environment.
- Attach the exact built package to the GitHub Release.
- Do not overwrite or move published version tags.
- Preserve commit, tag, release, and package traceability.