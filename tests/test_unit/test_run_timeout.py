import time

import pytest

from runner.cancellation import CancellationReason, CancellationToken
from runner.run_timeout import RunTimeoutWatchdog


def test_watchdog_requests_cancellation_on_timeout():
    """Acceptance scenario.

    Given an active token has a short watchdog deadline.
    When the deadline expires while the test polls with a bounded wait.
    Then the token records RUN_TIMEOUT cancellation.
    """
    token = CancellationToken()

    watchdog = RunTimeoutWatchdog(timeout_seconds=0.1, cancellation_token=token)

    try:

        watchdog.start()

        deadline = time.monotonic() + 2

        while not token.is_cancelled and time.monotonic() < deadline:

            time.sleep(0.01)

        assert token.is_cancelled is True

        assert token.reason == CancellationReason.RUN_TIMEOUT

    finally:
        watchdog.stop()


def test_watchdog_stop_prevents_timeout():
    """Acceptance scenario.

    Given a watchdog has started with an active token.
    When stop signals and joins the watchdog thread.
    Then the token remains active and the watchdog is no longer running.
    """
    token = CancellationToken()

    watchdog = RunTimeoutWatchdog(timeout_seconds=0.2, cancellation_token=token)

    watchdog.start()

    watchdog.stop()

    assert token.is_cancelled is False

    assert watchdog.is_running is False


def test_watchdog_cannot_start_twice():
    """Acceptance scenario.

    Given a watchdog has already started.
    When start is called again.
    Then RuntimeError rejects the second start and finally stops the watchdog.
    """
    token = CancellationToken()

    watchdog = RunTimeoutWatchdog(timeout_seconds=1, cancellation_token=token)

    try:

        watchdog.start()

        with pytest.raises(RuntimeError):
            watchdog.start()

    finally:
        watchdog.stop()


def test_watchdog_does_not_overwrite_existing_cancellation_reason():
    """Acceptance scenario.

    Given a token already records USER_REQUEST.
    When a watchdog deadline expires on that token.
    Then the original USER_REQUEST reason remains unchanged.
    """
    token = CancellationToken()

    token.cancel(CancellationReason.USER_REQUEST)

    watchdog = RunTimeoutWatchdog(
        timeout_seconds=0.05,
        cancellation_token=token,
    )

    try:
        watchdog.start()

        time.sleep(0.1)

    finally:
        watchdog.stop()

    assert token.is_cancelled is True

    assert token.reason == CancellationReason.USER_REQUEST


def test_run_timeout_reason_cannot_be_overwritten_by_user_cancel():
    """Acceptance scenario.

    Given a token first receives RUN_TIMEOUT.
    When USER_REQUEST is submitted afterward.
    Then the second cancellation is rejected and RUN_TIMEOUT remains recorded.
    """
    token = CancellationToken()

    first = token.cancel(CancellationReason.RUN_TIMEOUT)

    second = token.cancel(CancellationReason.USER_REQUEST)

    assert first is True
    assert second is False

    assert token.is_cancelled is True

    assert token.reason == CancellationReason.RUN_TIMEOUT


@pytest.mark.parametrize(
    "timeout_seconds",
    [0, -1, -0.1],
)
def test_watchdog_rejectes_invalid_timeout(timeout_seconds):
    """Acceptance scenario.

    Given a timeout is zero or negative.
    When a watchdog is constructed.
    Then ValueError rejects the timeout.
    """
    token = CancellationToken()

    with pytest.raises(ValueError):
        RunTimeoutWatchdog(timeout_seconds=timeout_seconds, cancellation_token=token)
