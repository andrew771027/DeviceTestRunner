# Device Test Runner v1.7.0 — Static Variable Substitution Integration Guide

## Purpose and implementation

Static variable substitution resolves allowlisted `${{ ... }}` placeholders before execution, after the run directory exists. The resolver does not use `eval`, execute shell commands, evaluate arithmetic, read environment variables, or recursively resolve variable values.

The implementation is already integrated into this repository:

- `runner/variables.py`: validates definitions, resolves placeholders, and checks field types.
- `runner/models.py`: stores `RunnerConfig.variables` and allows `int | float | str` for declared step timeouts.
- `runner/config.py`: validates variables during YAML loading and preserves unresolved templates.
- `runner/runner.py`: creates the run directory and resolves a new configuration before starting the watchdog or lifecycle steps.

The paths in this guide refer to this repository. No replacement files from a separate `src/runner` package or model patch are required.

## YAML example

```yaml
test_case:
  id: static_variables_001
  name: Static Variables Example
  description: Generate and validate a CSV using static variables

device:
  serial: emulator-5554
  product: pixel
  build: debug

variables:
  power: 110
  voltage: 4.2
  test_duration: 5
  cleanup_duration: 0.5
  output_name: power_result.csv

run_timeout_seconds: 60
cleanup_timeout_seconds: 10

retry:
  max_attempts: 1
  delay_seconds: 0
  retry_on: []

lifecycle:
  global_setup: {steps: []}
  setup: {steps: []}
  scenario:
    steps:
      - name: write_power_csv
        type: command
        command: |
          printf 'timestamp,power,voltage\n1,${{ vars.power }},${{ vars.voltage }}\n' > "${{ run.dir }}/${{ vars.output_name }}"
        timeout_second: '${{ vars.test_duration }}'
  teardown:
    steps:
      - name: show_output_path
        type: command
        command: 'echo "Artifact saved to ${{ run.dir }}/${{ vars.output_name }}"'
        timeout_second: '${{ vars.cleanup_duration }}'
  global_teardown: {steps: []}

artifact:
  output_dir: ./artifacts
  validation:
    rules:
      - name: power_result
        type: csv_content
        path: '${{ run.dir }}/${{ vars.output_name }}'
        required: true
        required_columns: [timestamp, power, voltage]
        min_rows: 1
```

Save the example as a YAML file, then pass it to the runner:

```bash
python3 main.py --config="path/to/config.yaml"
```

The command writes the CSV to the same resolved path used by artifact validation. `artifact.output_dir` defines the parent directory; `${{ run.dir }}` identifies the individual run directory as an absolute path.

## Supported fields and expressions

Substitution applies to these fields only:

| Field | Required resolved type |
| --- | --- |
| Lifecycle step `command` | String |
| Lifecycle step `timeout_second` | Finite positive integer or float |
| Artifact validation rule `path` | String |

All lifecycle stages are resolved, including teardown and global teardown. All artifact validation rule paths are resolved before execution, including rules associated with `after_step`.

Only `vars.NAME` and `run.dir` are recognized. Substitution does not apply to arbitrary configuration fields, including `artifact.output_dir`, `run_timeout_seconds`, or `cleanup_timeout_seconds`. In particular, `artifact.output_dir` must be known before the runner can create `run.dir`.

## Variable and type rules

- `variables` is optional and defaults to an empty mapping.
- Names must match `[A-Za-z_][A-Za-z0-9_]*`.
- Values may be strings, integers, floats, or booleans. Lists, mappings, and null values are rejected.
- A whole placeholder preserves the original type: `${{ vars.test_duration }}` resolves to integer `5`, and `${{ vars.cleanup_duration }}` resolves to float `0.5`.
- An embedded placeholder produces a string: `--power ${{ vars.power }}` becomes `--power 110`.
- `timeout_second` rejects numeric strings, booleans, zero, negative values, NaN, and infinity.
- `command` and `path` reject whole placeholders whose values are not strings.
- Whitespace around an expression is allowed, for example `${{ run.dir }}`.
- Undefined variables, unsupported expressions, and malformed placeholders raise `VariableResolutionError`.
- Variable values containing `${{` are rejected; recursive references are unsupported.

Arithmetic, nested references, dynamic step outputs, variable precedence, `env.*`, and secret references are outside the current feature scope.

## Resolution order and integration details

```text
YAML
  -> ConfigLoader: validate variables and retain templates
  -> RunnerConfig: unresolved configuration
  -> ArtifactManager.create_run_directory()
  -> StaticVariableResolver(variables, run_dir)
  -> resolved configuration copy
  -> watchdog and lifecycle execution
  -> cleanup, artifact validation, and report
```

Resolution happens in two phases because `run.dir` is unavailable during YAML loading. `ConfigLoader._load_steps()` preserves timeout placeholders instead of converting them to integers prematurely.

`RunnerConfig` stores the definitions with a default factory:

```python
variables: dict[str, str | int | float | bool] = field(default_factory=dict)
```

`ConfigLoader` validates these definitions with `StaticVariableResolver` and supplies a copy to `RunnerConfig`. After creating the run directory, `DeviceTestRunner.run()` resolves only the allowlisted dataclasses:

```python
from dataclasses import replace
from runner.variables import StaticVariableResolver

resolver = StaticVariableResolver(config.variables, run_dir)
config = replace(
    config,
    lifecycle=resolver.resolve_dataclass(config.lifecycle, path="lifecycle"),
    artifact=replace(
        config.artifact,
        validation=resolver.resolve_dataclass(
            config.artifact.validation, path="artifact.validation"
        ),
    ),
)
```

The original configuration is not mutated. Retries within a run use the resolved values, while a later call to `run()` resolves the original templates against its own run directory. All execution, cleanup, and validation consumers use the resolved copy.

The loader requires `artifact.output_dir` and a `steps` list for each lifecycle stage. Use `{steps: []}` for stages without commands.

## Failure and reporting behavior

Invalid variable definitions fail during YAML loading. Resolution errors fail before any test subprocess or watchdog starts. The run directory may already exist, but configuration resolution errors propagate as `VariableResolutionError` without producing a normal FAILED run or JSON report.

Executed commands are recorded as resolved `StepResult.command` values, and artifact validation results contain resolved paths. Static substitution does not change the reporter schema or add a dedicated variables metadata field.

## Shell command handling

Static substitution does not escape shell arguments. When commands are executed with `shell=True`, substituted values can introduce shell metacharacters. Use trusted YAML and quote paths appropriately, as shown in the example. Do not store secrets in variables because resolved commands may appear in reports and logs.

The resolver itself never executes variable values. Argument-list execution with `shell=False` is a possible future executor improvement.

## Verification

Run the resolver unit tests and static-variable integration tests:

```bash
python -m pytest -q tests/test_unit/test_variables.py
python -m pytest -q tests/test_integration/test_integration_static_variables.py
```

The tests cover type preservation, positive integer and float timeouts, interpolation, invalid definitions and expressions, immutable configuration resolution, subprocess CSV generation, artifact validation, JSON reporting, and distinct run directories.

To run the complete repository suite:

```bash
python -m pytest -q
```
