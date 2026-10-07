import time

from runner.cancellation import CancellationReason, CancellationToken
from runner.cleanup import CleanupTimeoutWatchdog


def test_cleanup_watchdog_uses_cleanup_timeout_reason():
    """Acceptance scenario.

    Given a cleanup watchdog has a half-second deadline.
    When the watchdog runs while the test polls for cancellation.
    Then the token is cancelled with CLEANUP_TIMEOUT.
    """

    token = CancellationToken()

    watchdog = CleanupTimeoutWatchdog(
        timeout_seconds=0.5,
        cancellation_token=token,
    )

    try:

        watchdog.start()

        deadline = time.monotonic() + 1

        while not token.is_cancelled and time.monotonic() < deadline:

            time.sleep(0.01)

    finally:

        watchdog.stop()

    assert token.is_cancelled is True

    assert token.reason == CancellationReason.CLEANUP_TIMEOUT
