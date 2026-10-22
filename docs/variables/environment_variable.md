# Device Test Runner v1.7.1 — Environment Variables

## Goal

Extend the existing v1.7.0 static resolver with `${{ env.NAME }}`.

```yaml
variables:
  repeat: 3
  test_duration: 600
  output_name: power_result.csv

test_case:
  id: env_demo
  name: Environment demo
  description: Uses a workstation-provided serial

device:
  serial: "${{ env.DEVICE_SERIAL }}"
  product: pixel
  build: test

retry:
  max_attempts: 1
  delay_seconds: 0
  retry_on: []

lifecycle:
  global_setup:
    steps: []
  setup:
    steps: []
  scenario:
    steps:
      - name: collect
        type: command
        command: "python run.py --repeat ${{ vars.repeat }}"
        timeout_second: "${{ vars.test_duration }}"
  teardown:
    steps: []
  global_teardown:
    steps: []

artifact:
  output_dir: ./artifacts
  validation:
    rules:
      - name: output
        type: exists
        path: "${{ run.dir }}/${{ vars.output_name }}"
        required: true
```

## Run

```bash
export DEVICE_SERIAL=ABCD1234
python -m pytest -q tests/test_env_variables.py tests/test_static_variables_e2e.py
```

The sample YAML illustrates substitution only; its `run.py` must be supplied separately to run it as a real scenario.

## Design

1. `ConfigLoader` reads YAML into an *unresolved* `RunnerConfig`.
2. `DeviceTestRunner.run()` snapshots `os.environ` once through `StaticVariableResolver`.
3. `device.serial` is resolved before allocating an artifact directory. Undefined environment names raise `VariableResolutionError`.
4. ArtifactManager creates `run.dir`.
5. The same resolver instance updates `run.dir` and resolves lifecycle commands, timeouts, and artifact paths.
6. The existing retry, cancellation, cleanup, validation and reporting paths are unchanged.

Supported expressions: `${{ env.NAME }}`, `${{ vars.NAME }}`, `${{ run.dir }}`. Names must match `[A-Za-z_][A-Za-z0-9_]*`.

### Environment versus YAML variables

`vars.*` preserves YAML primitive types; `env.*` always returns strings. Thus `${{ env.TIMEOUT }}` **does not** automatically become a numeric `timeout_second`. Continue using `vars.test_duration` for typed timeouts in v1.7.1.

### Snapshot semantics

Changes to `os.environ` after a run begins do not affect that run. The next run takes a new snapshot.

### Failure behavior

Missing variables and malformed expressions fail before execution. An empty but defined environment variable is **not** considered missing. For device serial, an empty string is generally invalid for real hardware; enforce device-specific validation before dispatch.

### Security

Environment variables are not automatically secrets. **Do not put credentials in templated commands, device metadata, or artifact paths**: they can appear in logs, subprocess arguments and JSON reports. No `${{ env.* }}` secret masking is implemented. Use dedicated credential passing instead.

### Limits

- No default values, nested references, expressions, or recursion.
- Only `device.serial`, lifecycle `command`/`timeout_second`, and artifact rule `path` are allowlisted.
- No implicit shell escaping. When inserting env values into shell commands, consider shell injection; use safe argument lists in a future executor design.
- This feature does not auto-discover physical devices; it reads values supplied by the host environment.
- `run.dir` is still resolved only after ArtifactManager creates it.

## Tests

```bash
PYTHONPATH=. pytest -q tests/test_env_variables.py tests/test_static_variables_e2e.py
```

Tests include: successful device serial in final report, missing variable fails before artifact directory creation, snapshot stability, invalid syntax, empty variable, typed timeout guard, and v1.7.0 regression.
