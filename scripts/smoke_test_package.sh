#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 0 ]]; then
    echo "Usage: bash scripts/smoke_test_package.sh" >&2
    exit 1
fi

shopt -s nullglob
WHEELS=(dist/*.whl)

if [[ ${#WHEELS[@]} -ne 1 ]]; then
    echo "Expected exactly one wheel in dist/, found ${#WHEELS[@]}" >&2
    exit 1
fi

VENV_PATH="$(mktemp -d "${TMPDIR:-/tmp}/dtr-release-test.XXXXXXXX")"
trap 'rm -rf -- "${VENV_PATH}"' EXIT

echo "==> Creating clean virtual environment"
python3 -m venv "${VENV_PATH}"

PYTHON="${VENV_PATH}/bin/python"

echo "==> Upgrading pip"
"${PYTHON}" -m pip install --upgrade pip

echo "==> Installing built wheel"

"${PYTHON}" -m pip install "${WHEELS[0]}"

echo "==> Checking installed package metadata and import"

"${PYTHON}" -I - <<'PY'
from importlib.metadata import version

import runner

package_version = version("devicetestrunner")
print(f"Installed devicetestrunner version: {package_version}")
print(f"Imported runner from: {runner.__file__}")
PY

echo "==> Package smoke test passed"
