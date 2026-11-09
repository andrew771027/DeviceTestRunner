# GitHub Actions Release Pipeline

## Overview

Device Test Runner uses a tag-driven GitHub Actions release workflow.

A release represents a specific, validated Device Test Runner source revision and its distributable Python packages.

The release process is separated from normal CI and is defined in
[release.yml](../../.github/workflows/release.yml). The sequence below is the
intended flow. Current blocking issues are listed under “Current Workflow
Limitations”; a successful release has not been verified.

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
`poetry version -s`. The current comparison has a typo and fails even when
the versions match; see “Current Workflow Limitations”.

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
wheel and attempts an import:

```bash
python -m venv /tmp/dtr-release-test
/tmp/dtr-release-test/bin/python -m pip install --upgrade pip
/tmp/dtr-release-test/bin/python -m pip install dist/*.whl
/tmp/dtr-release-test/bin/python -c "import device_test_runner"
```

The configured import is `device_test_runner`, while `pyproject.toml` packages
`runner`. This needs correction. The command also runs from the checkout;
an import of `runner` there could resolve source files. Run validation outside
the checkout to confirm the installed wheel is used. No CLI smoke command is
configured.

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
Release using `gh`, authenticated by `GH_TOKEN: ${{ github.token }}`. Its
current shell command has a missing line continuation; the example below
shows the intended command.

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

## Current Workflow Limitations

The checked-in workflow has these blocking issues:

| Step | Current issue | Required correction |
| --- | --- | --- |
| Validate tag matches package version | Compares the literal `"4{TAG_VERSION}"` | Use `"${TAG_VERSION}"` |
| Run release validation tests | Installs Poetry but not project dependencies before pytest | Install project dependencies before tests |
| Smoke test built wheel | Imports `device_test_runner`, while the packaged module is `runner` | Import `runner` outside the checkout after installing the wheel |
| Create Github Release | Missing trailing `\` after `gh release create "${GITHUB_REF_NAME}"` | Continue the command onto the asset and option lines as shown above |

The final shell issue can leave a Release created without assets before the
step fails. Inspect the run and its Release before retrying. These findings
come from source inspection; no GitHub Actions run or published release was
verified for this documentation update.

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
