# Device Test Runner v1.7.0 Acceptance Criteria

Version scope: Static Variable Substitution. These criteria describe the inspected working tree; [test matrix](../test_matrix/test_matrix_v1.7.0.md) distinguishes direct tests from source inspection.

## Configuration and substitution

- Omitted variables use an empty mapping. Definitions accept str, int, float and bool; names match `[A-Za-z_][A-Za-z0-9_]*`. Invalid mapping/name/value and recursive templates raise VariableResolutionError.
- `${{ vars.NAME }}` references a declared value. `${{ run.dir }}` resolves to the individual run's absolute directory. Repeated references are supported.
- Whole references preserve type; embedded references produce strings. Commands and paths resolve to strings; step timeouts resolve to finite positive int or float.
- Numeric timeout strings, bool, zero, negative, NaN and infinity are rejected before execution.
- Only lifecycle command/timeout_second and artifact validation path are substituted. Definitions are validated on load; templates are resolved after run directory creation.
- No recursive references, literal escaping, arithmetic, environment/secret references or arbitrary config substitution is supported.

## Execution and artifacts

- Resolution completes before watchdogs or test subprocesses start. Invalid expressions/types propagate without normal step execution or JSON reporting; the created run directory may remain.
- Resolution creates a new configuration without modifying original templates. Reusing the original configuration creates separate output paths for separate runs.
- The provided static-variable example generates a CSV, passes validation, and writes a PASSED report with resolved command and validation path.
- Package version and runtime/report runner_version identify 1.7.0.
- Controlled lifecycle, cancellation, cleanup, required/optional artifacts and selective retry retain their current behavior.

## Conclusion and release boundary

Actual local commands and results are recorded in [Definition of Done](../definition_of_done/definition_of_done_v1.7.0.md). Acceptance is based on inspected source, direct resolver/integration assertions and local full-suite verification. The test matrix documents untested boundaries; this does not establish all-platform guarantees or release publication.

Tag, GitHub Release, issue/milestone state, Linux verification and distribution installation remain separate checks. Existing exception-finalization and CLI TIMED_OUT exit-code limitations remain open.
