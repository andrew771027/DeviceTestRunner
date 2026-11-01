# Device Test Runner v1.7.2 — Runtime Context

## Purpose

Reuse resolved device metadata in lifecycle commands and artifact validation paths. The runner resolves serial, binds serial/product/build once, then resolves the remaining configuration before execution. This does not discover or select a device.

## Device-free example

Save this complete YAML as `configs/runtime_context.yaml`. It uses POSIX shell `printf`, requires no device or user script, and writes the resolved identity to an artifact. Run from the project root:

```bash
export DEVICE_SERIAL=demo-172
poetry run python main.py --config configs/runtime_context.yaml
```

```yaml
test_case: {id: runtime_context, name: Device identity, description: Write resolved metadata.}
device:
  serial: "${{ env.DEVICE_SERIAL }}"
  product: demo
  build: local
variables:
  output_name: identity.txt
lifecycle:
  global_setup: {steps: []}
  setup: {steps: []}
  scenario:
    steps:
      - name: identity
        type: command
        command: >-
          printf '%s\n' "${{ device.serial }}" "${{ device.product }}" "${{ device.build }}"
          > "${{ run.dir }}/${{ vars.output_name }}"
        timeout_second: 5
  teardown: {steps: []}
  global_teardown: {steps: []}
artifact:
  output_dir: artifacts/runtime_context
  validation:
    rules:
      - name: identity
        type: exists
        path: "${{ run.dir }}/${{ vars.output_name }}"
        required: true
```

Open the run directory under `artifacts/runtime_context/`. `identity.txt` contains demo-172, demo and local on separate lines. `result.json` reports PASSED and metadata.device_serial is demo-172. Commands run in a shell: use trusted values and quote paths; substitution itself does not escape arguments.

## References and fields

| Reference | Source / type | Supported destination |
| --- | --- | --- |
| `${{ device.serial }}` | Resolved device.serial; string | Lifecycle command and validation path |
| `${{ device.product }}` | Literal device.product; string | Lifecycle command and validation path |
| `${{ device.build }}` | Literal device.build; string | Lifecycle command and validation path |

These references require device metadata, not an additional context YAML section. Existing vars, env and run.dir references remain available. Whole device references return strings, so they fail timeout_second's numeric check. All lifecycle stages and all validation paths, including after_step rules, are resolved eagerly. Other fields such as artifact.output_dir and expected_json_values are outside substitution scope.

## Resolution lifecycle

1. ConfigLoader validates variables and preserves runtime templates.
2. DeviceTestRunner creates one StaticVariableResolver using a host environment snapshot and startup cwd.
3. Resolve device.serial through the existing DeviceInfo allowlist; product and build stay literal.
4. bind_device checks all three values are non-empty strings without `${{`, then copies them once.
5. ArtifactManager creates the run directory; the same resolver receives its actual absolute path.
6. Resolve lifecycle command/timeout_second and validation path copies; start watchdogs and execution only after success.
7. Existing retry, cleanup, validation and reporting consume the resolved copy. The caller's configuration retains its templates.

A new run constructs a new resolver and snapshot. Retries reuse resolved values. SubprocessExecutor separately copies live os.environ for each execution and adds its own environment fields; template snapshots do not configure subprocess environments.

## Errors and compatibility

- All three device fields are required by YAML loading and must be non-empty resolved strings at run time, even without templates. Product/build templates are rejected, not resolved. Whitespace-only strings currently pass because no trimming occurs.
- Env lookup permits an empty value, but binding an empty serial fails. Missing env values also fail before run directory allocation. ArtifactManager initialization may already create the output parent.
- Serial cannot reference device context: binding has not happened yet. run.dir in serial currently returns startup cwd; reserve it for later commands and validation paths.
- Unknown device fields, lookup before binding and a second bind_device call raise VariableResolutionError.
- Binding failures occur before the run subdirectory is created. Command/path lookup failures occur after allocation and can leave an empty directory. Both propagate without a normal FAILED result or result.json; CLI currently shows a traceback.
- The binding API copies values and rejects rebinding. Its public device_context is a Python dictionary, not a mechanically immutable mapping.
- No recursive substitution, expressions, context.* namespace, step output, run.id, device discovery, environment mapping or secret masking is provided. Commands can appear in logs and reports.

## Verification and boundaries

```bash
poetry run pytest -q tests/test_unit/test_runtime_context.py
poetry run pytest -q tests/test_integration/test_integration_static_variables.py
```

Unit cases cover command interpolation, retained input, run.dir/vars paths, unbound and unknown lookups, rebinding, invalid serial metadata and snapshot stability. The successful context integration case uses real YAML loading, a subprocess, CSV validation and JsonReporter, but does not read back its JSON or assert CSV cell contents. Its unknown-field case asserts an exception and absence of result.json, without an executor spy. Product/build validation and dictionary mutability details above come from source inspection, not dedicated tests. See the [test matrix](../test_matrix/test_matrix_v1.7.2.md) and [verification record](../definition_of_done/definition_of_done_v1.7.2.md).
