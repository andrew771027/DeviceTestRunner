# Device Test Runner v1.7.1 — Environment Variables

Historical scope: v1.7.1. For current device binding and the non-empty serial/product/build requirement, see the [v1.7.2 Runtime Context guide](runtime_context.md). Empty environment values remain valid lookups but cannot be bound as serial.

## Run a device-free example

Save this complete YAML as `configs/env_demo.yaml`:

```yaml
test_case: {id: env_demo, name: Environment demo, description: Read a host serial.}
device:
  serial: '${{ env.DEVICE_SERIAL }}'
  product: demo
  build: demo
variables:
  duration: 5
lifecycle:
  global_setup: {steps: []}
  setup: {steps: []}
  scenario:
    steps:
      - name: show_serial
        type: command
        command: 'echo "${{ env.DEVICE_SERIAL }}" > "${{ run.dir }}/serial.txt"'
        timeout_second: '${{ vars.duration }}'
  teardown: {steps: []}
  global_teardown: {steps: []}
artifact:
  output_dir: artifacts/env_demo
  validation:
    rules:
      - name: serial_file
        type: exists
        path: '${{ run.dir }}/serial.txt'
```

From the repository root:

```bash
export DEVICE_SERIAL=demo-001
poetry run python main.py --config configs/env_demo.yaml
```

No physical device is needed. The run directory contains serial.txt and result.json; expect summary.status PASSED and metadata.device_serial demo-001. This feature reads a supplied serial; it does not discover or validate hardware.

## Fields and values

| Reference / field | Required / default | Behavior |
| --- | --- | --- |
| `${{ env.NAME }}` | Host must supply each referenced name; no default | Always a string; empty is defined, missing raises VariableResolutionError |
| `device.serial` | Required; no default | String; supports vars and env before run directory allocation |
| Lifecycle `command` | Required per step | String; supports vars, env and run.dir |
| Lifecycle `timeout_second` | Optional; YAML default 60 | Finite positive int/float; env numeric strings are rejected; use typed vars |
| Validation rule `path` | Required per rule | String; supports vars, env and run.dir |

Names match `[A-Za-z_][A-Za-z0-9_]*`. No default expression, arithmetic, recursive templates, secret namespace, or custom run/step environment mapping is implemented. product, build, output_dir, scope timeouts and retry settings are not substituted. Inserting a value does not escape shell syntax or mask it in commands, logs or reports.

## Resolution and failures

1. ConfigLoader validates variable definitions and retains unresolved field templates.
2. DeviceTestRunner.run constructs a resolver with one copy of os.environ and the current working directory as the initial run_dir.
3. It resolves device.serial in a new config copy before creating the run subdirectory. Missing env names here produce no run directory or result.json. ArtifactManager construction can already create the output parent.
4. ArtifactManager creates the run directory. The same resolver updates run_dir, then resolves all lifecycle commands/timeouts and validation paths.
5. Watchdogs and subprocesses start only after resolution succeeds. Later field errors may leave the run directory, without result.json.
6. Retries reuse resolved values; another run creates a new snapshot. Original configuration templates remain unchanged.

Use run.dir in commands and validation paths. In device.serial it currently resolves to the startup working directory because serial resolution occurs before artifact allocation.

The snapshot applies to template resolution. SubprocessExecutor separately copies live os.environ for each execute call, then supplies DEVICE_TEST_RUNNER_ROOT and RUN_ARTIFACT_DIR. These executor values are not automatically available as template env names in the runner snapshot. No entire environment snapshot is written to reports, but rendered values can appear in metadata, command strings and artifact paths.

## Verification

```bash
poetry run pytest -q tests/test_unit/test_env_variables.py tests/test_integration/test_integration_static_variables.py
```

The [v1.7.1 matrix](../test_matrix/test_matrix_v1.7.1.md) distinguishes direct assertions from inspected behavior. Full configuration and report reference: [user manual](../user_manual.md). Historical static feature: [v1.7.0 guide](static_variable_substitution.md).
