# Device Test Runner v1.6.3 Acceptance Criteria

Version scope: Cancellation-Aware Cleanup. These criteria describe the inspected source and local tests, not a published release. Test mappings and evidence limits are in the [test matrix](../test_matrix/test_matrix_v1.6.3.md).

## Configuration

- Missing/null cleanup_timeout_seconds means no overall cleanup deadline; YAML values must be finite positive numbers and must not be booleans.
- Run timeout and each step timeout remain separate settings.
- Loader wiring is source-inspected; negative/non-finite/boolean cleanup inputs and missing values have direct parser tests. Full YAML cleanup value coverage remains incomplete.

## Lifecycle and deadlines

- Run cancellation stops normal global_setup/setup/scenario work and new attempts.
- Successful global_setup establishes the condition for teardown, including cancellation before setup starts.
- Global_teardown is attempted even when global_setup failed or the run was cancelled before starting, unless the cleanup token is cancelled.
- Cleanup uses a fresh token shared across both cleanup stages, attempts and retry delays.
- Ordinary cleanup step failure permits later cleanup work; cleanup deadline cancels the running attempt and prevents new cleanup work.
- Step timeout yields TIMEOUT without implying cleanup scope timeout. Cleanup interruption yields a CANCELLED attempt and cleanup_summary with timed_out=true and cancellation_reason=cleanup_timeout.

## Artifacts, status and reports

- Cancelled attempts are not retried and skip attempt-level validation.
- Final validation still runs after controlled cleanup and preserves invalid partial CSV and missing artifact results.
- Original RUN_TIMEOUT produces TIMED_OUT and USER_REQUEST produces CANCELLED even if cleanup or required artifacts fail.
- Without run cancellation, cleanup failure produces FAILED.
- result.json includes cleanup_summary: attempted, timed_out, failed, cancellation_reason. Metadata retains the original run cancellation reason; cleanup_timeout_seconds is not a metadata field.
- Empty cleanup stages can set attempted=true; this field does not prove a process launched.

## Conclusion and remaining evidence

Local full-suite results are recorded in [Definition of Done](../definition_of_done/definition_of_done_v1.6.3.md). The source implements the intended controlled cleanup flow. The unmatched quote in the run/cleanup timeout fixture and non-creating `touch -c` marker limit two tests' conclusions. Stronger assertions are needed before treating those cases as complete deadline/skip evidence.

Exception-safe finalization, Linux validation, detached processes, CLI TIMED_OUT exit code and release checks remain open. No hard return-time guarantee is made: process termination, output draining, validation and reporting can extend beyond deadlines.
