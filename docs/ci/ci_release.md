# GitHub Actions Release Pipeline

## Overview

Device Test Runner uses a tag-driven GitHub Actions release workflow.

A release represents a specific, validated Device Test Runner source revision and its distributable Python packages.

The release process is separated from normal CI and is defined in
[release.yml](../../.github/workflows/release.yml). The sequence below is the
intended flow. Recovery from a partially created Release is described below; a successful
end-to-end release has not been verified.

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
Main ancestry / version checks / pytest
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

The intended check removes the leading `v` and compares the result with
`poetry version -s`. A mismatch causes the workflow to fail.

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

Pushing the tag triggers the release workflow. Resolve the current workflow
limitations before publishing a release tag.

## Release Workflow Trigger

```yaml
on:
  push:
    tags:
      - "v*.*.*"
```

Normal pushes to `main` do not create releases. There is no manual trigger.
The tag filter is a glob, not strict semantic version validation.

## Release Validation

The single `release` job (`Build and Release`) runs on `ubuntu-latest` and
selects Python 3.12. It checks out full history (`fetch-depth: 0`), fetches
`origin/main`, installs Poetry using `python -m pip install Poetry` without a
version pin, and prints the tag.

Before building, the workflow intends to verify:

```text
Tagged commit belongs to main
Tag matches package version
Automated tests pass
```

The ancestry check uses `git merge-base --is-ancestor` against `origin/main`.
An older ancestor is allowed; the tag need not point to the branch tip. The
workflow does not configure branch protection or query PR Quality Gate results.

Before testing, `poetry install --no-interaction` installs the project and its
locked dependencies, including pytest, into the Poetry environment. Installing
Poetry alone does not install pytest.

Tests use `poetry run pytest`, without marker filters or coverage options.
No release test-report upload is configured.

## Package Build

The package is built using Poetry:

```bash
poetry build
```

Expected output:

```text
dist/
├── devicetestrunner-<version>-py3-none-any.whl
└── devicetestrunner-<version>.tar.gz
```

The wheel is the built Python distribution.

The `.tar.gz` file is the source distribution.

## Package Smoke Test

The workflow creates a clean virtual environment, upgrades pip, installs the
wheel and imports its `runner` module:

```bash
python -m venv /tmp/dtr-release-test
/tmp/dtr-release-test/bin/python -m pip install --upgrade pip
/tmp/dtr-release-test/bin/python -m pip install dist/*.whl
cd /tmp/dtr-release-test
/tmp/dtr-release-test/bin/python -I -c "import runner; print(runner.__file__)"
```

The distribution is named `devicetestrunner`, while `pyproject.toml` packages
the Python module `runner`. The import runs outside the checkout with `-I`
(isolated mode), which excludes the working directory and `PYTHONPATH` from
module lookup. Printing `runner.__file__` shows the installed module location.
No CLI smoke command is configured.

## Package Artifact

Built packages are stored as GitHub Actions artifacts for build traceability.

Example:

```text
device-test-runner-v1.7.3
```

Contents:

```text
devicetestrunner-1.7.3-py3-none-any.whl
devicetestrunner-1.7.3.tar.gz
```

The upload uses `actions/upload-artifact@v7`, selects `dist/*whl` and
`dist/*.tar.gz`, retains files for **30 days**, and fails if no files are found.
It has no `if: always()` override and runs only after preceding steps succeed.

Workflow artifacts are temporary CI artifacts and are not treated as the primary release distribution channel.

## GitHub Release

The workflow intends to attach the same built package files to the GitHub
Release using `gh`, authenticated by `GH_TOKEN: ${{ github.token }}`. The
asset paths and options belong to the same command through shell line
continuations:

The release is created using the existing Git tag.

```bash
gh release create v1.7.3 \
  dist/*.whl \
  dist/*.tar.gz \
  --verify-tag \
  --generate-notes \
  --title "Device Test Runner v1.7.3"
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

## Action Resolution Failure

`Unable to resolve action actions /setup-python, repository not found` is
caused by the space in `actions /setup-python`. The current workflow uses
`actions/setup-python@v7` without that space.

For this tag-triggered workflow, check the workflow file at the triggering
tag's commit. Rerunning the failed run uses the same Git ref and commit;
a correction on `main` alone does not update that tagged workflow. Follow
the release immutability policy below when preparing a corrected release.

## Recovering a Partially Created Release

A missing trailing `\` after `gh release create "${GITHUB_REF_NAME}"` causes
Bash to execute the wheel path as a separate command, producing
`Permission denied` (exit code 126). The supplied v1.7.3 run log shows the
Release URL before this failure: the create command succeeded without assets.
The current workflow includes the required continuation.

Rerunning `gh release create` for that tag will encounter the existing Release.
After downloading the original build's package artifact and verifying that
its wheel and source distribution match the release, attach those files from
the directory containing `dist/`:

```bash
gh release upload v1.7.3 dist/*.whl dist/*.tar.gz
```

This recovery command requires an authenticated GitHub CLI in the repository.
It does not overwrite existing assets. Preserve the original tag and build;
verify both attachments on the Release after upload. No remote recovery was
performed as part of this documentation update.

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
