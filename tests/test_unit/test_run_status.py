import pytest

from runner.cancellation import CancellationReason
from runner.run_status import calculate_run_status


@pytest.mark.parametrize(
    "reason, expected",
    [
        (
            CancellationReason.RUN_TIMEOUT,
            "TIMED_OUT",
        ),
        (
            CancellationReason.USER_REQUEST,
            "CANCELLED",
        ),
        (
            None,
            "PASSED",
        ),
    ],
)
def test_run_status_from_cancellation_reason(reason, expected):
    """Acceptance scenario.

    Given a run has the parameterized cancellation reason and no failures.
    When calculate_run_status evaluates its summary.
    Then the status matches TIMED_OUT, CANCELLED or PASSED for that reason.
    """
    status = calculate_run_status(
        cancellation_reason=reason,
        cleanup_failed=False,
        failed_steps=0,
        cancelled_steps=0,
        skipped_steps=0,
        failed_required_artifact_rules=0,
    )

    assert status == expected


def test_run_timeout_takes_priority_over_step_failure():
    """Acceptance scenario.

    Given RUN_TIMEOUT accompanies failed, cancelled and skipped steps.
    When the run status is calculated.
    Then TIMED_OUT takes priority over the other outcomes.
    """
    status = calculate_run_status(
        cancellation_reason=CancellationReason.RUN_TIMEOUT,
        cleanup_failed=False,
        failed_steps=1,
        cancelled_steps=1,
        skipped_steps=2,
        failed_required_artifact_rules=0,
    )

    assert status == "TIMED_OUT"


def test_user_cancellation_takes_priority_over_failure():
    """Acceptance scenario.

    Given USER_REQUEST accompanies failed steps.
    When the run status is calculated.
    Then CANCELLED takes priority over failure.
    """
    status = calculate_run_status(
        cancellation_reason=CancellationReason.USER_REQUEST,
        cleanup_failed=False,
        failed_steps=1,
        cancelled_steps=1,
        skipped_steps=2,
        failed_required_artifact_rules=1,
    )

    assert status == "CANCELLED"


@pytest.mark.parametrize(
    (
        "failed_steps",
        "cancelled_steps",
        "skipped_steps",
        "failed_required_artifact_rules",
        "expected_status",
    ),
    [
        (
            0,
            0,
            0,
            0,
            "PASSED",
        ),
        (
            1,
            0,
            0,
            0,
            "FAILED",
        ),
        (
            0,
            1,
            0,
            0,
            "CANCELLED",
        ),
        (
            0,
            0,
            1,
            0,
            "FAILED",
        ),
        (
            0,
            0,
            0,
            1,
            "FAILED",
        ),
    ],
)
def test_run_status_matrix(
    failed_steps,
    cancelled_steps,
    skipped_steps,
    failed_required_artifact_rules,
    expected_status,
):
    """Acceptance scenario.

    Given no cancellation reason and summary counts matching a parameterized row.
    When calculate_run_status evaluates that row.
    Then the result matches the expected status precedence.
    """
    status = calculate_run_status(
        cancellation_reason=None,
        cleanup_failed=False,
        failed_steps=failed_steps,
        cancelled_steps=cancelled_steps,
        skipped_steps=skipped_steps,
        failed_required_artifact_rules=(failed_required_artifact_rules),
    )

    assert status == expected_status
