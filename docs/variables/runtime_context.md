# Device Test Runner v1.7.2 — Runtime Context

## Learning objective

Expose already resolved `DeviceInfo` as an immutable runtime context. Reuse v1.7.0 `${{ vars.NAME }}` / `${{ run.dir }}` and v1.7.1 `${{ env.NAME }}`.

## YAML example

```yaml
variables:
  output_name: result.csv
  repeat: 3

test_case:
  id: runtime_context_001
  name: Runtime context demonstration
  description: Resolve device metadata before executing commands

device:
  serial: "${{ env.DEVICE_SERIAL }}"
  product: pixel
  build: development

retry:
  max_attempts: 1
  delay_seconds: 0
  retry_on: []

lifecycle:
  global_setup: {steps: []}
  setup: {steps: []}
  scenario:
    steps:
      - name: collect
        type: command
        command: "python run.py --serial ${{ device.serial }} --repeat ${{ vars.repeat }}"
        timeout_second: 600
  teardown: {steps: []}
  global_teardown: {steps: []}

artifact:
  output_dir: ./artifacts
  validation:
    rules:
      - name: result
        type: exists
        path: "${{ run.dir }}/${{ vars.output_name }}"
        required: true
```

`run.py` is a user-provided scenario script; the sample is a configuration illustration, not a runnable test without that script.

## Resolution lifecycle

1. `ConfigLoader.load()` parses YAML without replacing runtime expressions.
2. `DeviceTestRunner.run()` creates a single `StaticVariableResolver`, taking an environment snapshot.
3. Resolve `device.serial` (e.g. `${{ env.DEVICE_SERIAL }}`) using the resolver. `device.product` and `device.build` are left as literal values by the v1.7.1 allowlist.
4. `resolver.bind_device(config.device)` checks the three fields are non-empty resolved strings, then binds them **once**.
5. ArtifactManager creates the run directory; the resolver receives the actual `run.dir`.
6. Resolve lifecycle `command` and `timeout_second` plus artifact rule `path` with the same resolver.
7. Execute using the existing runner lifecycle, retry, cancellation, cleanup, validation and reporting mechanisms.

## New source changes

### `runner/variables.py`

- Add `device_context: dict[str, str] | None` initialized to `None`.
- Add `bind_device(device)` with one-time binding and validation.
- Extend `_lookup()` to support only `device.serial`, `device.product`, `device.build`.
- Unknown fields raise `VariableResolutionError`.

### `runner/runner.py`

Immediately after the v1.7.1 device resolution, call `resolver.bind_device(config.device)`. Bump `VERSION` to `1.7.2`. No changes are required to ConfigLoader or Executor for the new device context.

## Test strategy

```bash
python -m pip install pytest pyyaml
PYTHONPATH=. python -m pytest -q tests/
```

- Unit: resolved device serial, product, build; unbound context; unknown field; duplicate binding; unresolved or empty metadata; environment snapshot.
- Integration: YAML → ConfigLoader → Runner → real SubprocessExecutor → ArtifactValidator → JSON report; invalid context fails before starting subprocess.
- Regression: prior v1.7.0 and v1.7.1 test suites.

## Security and limitations

- Static substitution is **not shell quoting**. Device IDs inserted into a shell command must be trusted; an argument-array executor would be safer for arbitrary inputs.
- Never template secrets into commands or metadata: commands may be recorded in logs and reports.
- `device.serial` cannot refer to `${{ device.serial }}` while resolving itself; it must originate from a literal, `${{ vars.NAME }}`, or `${{ env.NAME }}`.
- This version intentionally does not support `${{ step.output }}`, `${{ run.id }}`, expressions, recursive variables, device discovery, or scheduling.
- Resolution failure after directory allocation may leave an empty run directory, but no test subprocess starts.
- `device.product` and `device.build` are literal config values in this version. Only `device.serial` is an allowed variable-bearing device field.
- The runner uses a one-time environment snapshot; changes in `os.environ` during the run do not affect context values.
