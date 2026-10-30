# Device Test Runner v1.7.2 Acceptance Criteria

Scope: Device Runtime Context, source `940fe66` and tests `2aeb559`. Evidence and test gaps are in the [test matrix](../test_matrix/test_matrix_v1.7.2.md).

## Configuration and execution

- ConfigLoader retains runtime templates. Runner creates one environment snapshot, resolves device.serial, and binds device identity before allocating the run directory.
- Serial, product and build must each be non-empty strings without unresolved template markers. Product/build remain literal. This validation applies to configurations without templates and to Python API configurations.
- Device context supports only serial, product and build. Unknown fields, lookup before binding and repeat binding raise VariableResolutionError.
- Lifecycle commands and validation paths may reference device identity alongside vars, env and run.dir. All stages and validation rules resolve before watchdogs or subprocess execution. Device references return strings and cannot provide a numeric step timeout.
- Original configuration templates remain intact. Retries reuse resolved values; each run constructs its own resolver. There is no device discovery or implicit subprocess environment assignment.
- Binding/serial failures precede run subdirectory creation; later command/path failures may leave an empty directory. Neither produces a normal FAILED result or result.json. The artifact output parent may already exist.
- Report schema stays unchanged; resolved identity appears in existing device metadata and executed commands contain substituted values. Package and runtime identify 1.7.2.

## Compatibility and conclusion

Empty serials that previously resolved from an existing env name now fail device binding. Empty, non-string or templated product/build also fail. Whitespace-only strings currently pass; no trimming occurs. bind_device copies values and rejects repeat binding, but its public dictionary is mutable in Python.

No context.*, step outputs, run.id, recursive substitution, environment mapping, shell escaping or secret masking is implemented. Subprocess environments still copy live os.environ independently.

Local regression results and example verification are recorded in [Definition of Done](../definition_of_done/definition_of_done_v1.7.2.md). Source-inspected rules with missing dedicated tests remain explicit in the matrix. Local acceptance does not establish remote CI, hardware behavior or a published release.
