# Device Test Runner v1.7.4 — Execution Manifest

## Objective

Persist a versioned, inspectable **resolved configuration snapshot** before subprocess execution, and link it to the execution result. This builds on v1.7.3's schema and cross-field validation and v1.7.0–v1.7.2's variable resolution.

## Execution sequence

1. `ConfigLoader.load()` parses YAML and validates schema and cross-field references.
2. `DeviceTestRunner.run()` keeps `original_config` and snapshots environment via `StaticVariableResolver`.
3. Resolve `DeviceInfo`, bind device context, allocate `run.dir`, resolve lifecycle and artifact rules.
4. `build_manifest()` serializes the original and resolved `RunnerConfig` dataclasses, masks referenced environment values, and computes canonical JSON SHA-256 fingerprints.
5. `save_manifest()` writes `execution_manifest.json` atomically with status `PREPARED` **before** the first subprocess.
6. Run lifecycle, cleanup, artifact validation and save `result.json` using the existing pipeline.
7. Rewrite manifest with `COMPLETED`, final result status and timestamp.

## Example

```yaml
test_case:
  id: power_test
  name: Power test
  description: Demonstrate manifest
device:
  serial: "${{ env.DEVICE_SERIAL }}"
  product: pixel
  build: test
variables:
  repeat: 3
  duration: 600
  output_name: power_result.csv
retry:
  max_attempts: 1
  delay_seconds: 0
  retry_on: []
lifecycle:
  global_setup: {steps: []}
  setup: {steps: []}
  scenario:
    steps:
      - name: power_test
        type: command
        command: "python run.py --serial ${{ device.serial }} --repeat ${{ vars.repeat }}"
        timeout_second: "${{ vars.duration }}"
  teardown: {steps: []}
  global_teardown: {steps: []}
artifact:
  output_dir: ./artifacts
  validation:
    rules:
      - name: power_csv
        type: exists
        path: "${{ run.dir }}/${{ vars.output_name }}"
        required: true
```

`run.py` in this illustrative YAML is user-supplied; it is not part of this package.

## Example manifest excerpt

```json
{
  "schema_version": 1,
  "runner_version": "1.7.4",
  "status": "COMPLETED",
  "source_config_sha256": "<64 hexadecimal characters>",
  "resolved_config_sha256": "<64 hexadecimal characters>",
  "resolved_config": {
    "variables": {"repeat": 3, "duration": 600, "output_name": "power_result.csv"}
  }
}
```

Only device, lifecycle and artifact.validation are resolved by the runner; other fields retain their configured values. The actual output includes the full configuration snapshot, platform details, timestamps, and run directory. The JSON excerpt is intentionally abbreviated.

## Fingerprint semantics

- Canonical JSON serialization uses `sort_keys=True` and compact separators; hashes are SHA-256 of the **redacted** normalized config.
- The original config hash is **not a raw YAML file hash**. Formatting and comments are not captured.
- Resolved config hash includes `run.dir` in resolved artifact paths; identical scenarios in different run directories can have different resolved hashes.
- A matching hash does not establish full experiment reproducibility: device firmware, APK/script revision, SDK version, toolchain, environment, and hardware state also matter.
- To compare semantic configuration across runs, use the original normalized config hash and inspect the resolved config; a future release can add a run-dir-independent semantic fingerprint.

## Secret handling

- Only environment values referenced by `${{ env.NAME }}` in the original config are considered for masking. Candidates are sorted by decreasing value length, but the current `_redact` string branch returns inside the loop after the first candidate, even when it does not match. Only that candidate can be replaced with `[REDACTED:env.NAME]`; multiple referenced values are not fully masked.
- This is **not a secure secrets implementation**. Literal secrets, transformed secrets, other logs, command arguments, and `result.json` may still expose sensitive values.
- Do not put credentials in YAML commands or artifacts. Use an appropriate secret delivery mechanism in a later release.
- The manifest may contain device identifiers and local paths; apply suitable access controls and retention rules.

## Failure behavior and limitations

- Variable resolution errors before manifest creation prevent manifest creation.
- If the process crashes after writing the `PREPARED` manifest, it can remain `PREPARED` (rather than `FAILED`).
- A normal cancellation or timeout that returns a `RunResult` produces `COMPLETED` with its actual result status.
- If reporter saving fails, the manifest remains `PREPARED`. If final manifest saving fails, the exception propagates even though result.json may exist.
- `os.replace()` provides atomic file replacement on the same filesystem, not an absolute guarantee against power-loss data loss; directory fsync is not implemented.
- This version does not record Git commit, source script hashes, APK hashes, Android build fingerprint, or package-lock information.

## Tests

```bash
python -m pip install pytest pyyaml
PYTHONPATH=. python -m pytest -q tests/
```

The new tests verify end-to-end manifest creation, redaction, stable hashes, hash changes, atomic overwrite, and invalid input. Existing v1.7.3 regression tests remain included.

## Future directions

- Explicit experiment ID and schema migration
- Git SHA, script/APK checksums and toolchain versions
- A stable semantic fingerprint independent of run directory
- Manifest failure finalization in an outer `finally`
- Full secret redaction across reporter/logging/arguments
- Re-run command generation after artifact and dependency verification

See the [field reference](../user_manual.md#檢查-execution-manifest), [test matrix](../test_matrix/test_matrix_v1.7.4.md) and [local verification](../definition_of_done/definition_of_done_v1.7.4.md).
