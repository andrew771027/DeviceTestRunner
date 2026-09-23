from runner.cancellation import CancellationReason


def calculate_run_status(
    *,
    cancellation_reason: CancellationReason | None,
    failed_steps: int,
    cancelled_steps: int,
    skipped_steps: int,
    failed_required_artifact_rules: int,
) -> str:

    if cancellation_reason == CancellationReason.RUN_TIMEOUT:
        return "TIMED_OUT"

    if cancellation_reason == CancellationReason.USER_REQUEST:
        return "CANCELLED"

    if cancelled_steps > 0:
        return "CANCELLED"

    if failed_steps > 0:
        return "FAILED"

    if skipped_steps > 0:
        return "FAILED"

    if failed_required_artifact_rules > 0:
        return "FAILED"

    return "PASSED"
