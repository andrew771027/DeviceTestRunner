# Device Test Runner v1.7.1 Acceptance Criteria

Baseline: `c1d457c`. These conditions describe inspected implementation; direct tests and gaps are in the [test matrix](../test_matrix/test_matrix_v1.7.1.md).

## Configuration and execution

- `${{ env.NAME }}` reads a run-local host environment snapshot; names match `[A-Za-z_][A-Za-z0-9_]*`. Undefined names raise VariableResolutionError; defined empty strings succeed.
- Env values remain strings. Numeric env references cannot become timeout_second; finite positive numeric literals or typed vars are required.
- device.serial resolves before run directory creation; serial errors produce no run subdirectory or result.json. ArtifactManager may already have created the output parent.
- The same resolver updates run.dir after allocation and resolves all lifecycle command/timeout fields and all validation paths before watchdogs or subprocesses start. These later errors can leave an empty directory without result.json.
- Resolution creates config copies. Loaded templates remain intact. Retry uses resolved values; another run constructs a fresh snapshot.
- Successful YAML-to-report execution places the resolved serial in metadata.device_serial and identifies runner_version as 1.7.1. Existing static variables, lifecycle, retry, cleanup and artifact behavior remain covered by the full suite.

## Limits and conclusion

Only serial, step command/timeout and validation path are allowlisted. No custom environment mappings, default-value expressions, recursive references, secret masking or implicit shell escaping is implemented. Executor copies live host environment independently for each execute call. run.dir in serial currently identifies startup cwd; use run.dir in commands and validation paths.

Local evidence and remaining checks are in [Definition of Done](../definition_of_done/definition_of_done_v1.7.1.md). Passing local tests does not establish Linux CI, hardware behavior, dependency lock consistency, installed distribution state or release publication.
