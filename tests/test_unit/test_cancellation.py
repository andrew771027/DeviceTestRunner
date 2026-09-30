import pytest

from runner.cancellation import CancellationReason, CancellationRequested, CancellationToken


def test_token_initial_state():
    """Acceptance scenario.

    Given a newly constructed cancellation token.
    When its state is read.
    Then is_cancelled is false and reason is None.
    """
    token = CancellationToken()

    assert token.is_cancelled is False
    assert token.reason is None


def test_token_can_be_cancelled():
    """Acceptance scenario.

    Given an active cancellation token.
    When cancel is called.
    Then is_cancelled becomes true.
    """
    token = CancellationToken()

    token.cancel()
    assert token.is_cancelled is True


def test_cancel_is_idempotent():
    """Acceptance scenario.

    Given an active cancellation token.
    When cancel is called twice.
    Then the token remains cancelled without an error.
    """
    token = CancellationToken()

    token.cancel()

    token.cancel()

    assert token.is_cancelled is True


def test_raise_if_cancelled_does_nothing_when_active():
    """Acceptance scenario.

    Given an active cancellation token.
    When raise_if_cancelled is called.
    Then no exception is raised.
    """
    token = CancellationToken()

    token.raise_if_cancelled()


def test_raise_if_cancelled_raises_after_cancel():
    """Acceptance scenario.

    Given a cancelled token.
    When raise_if_cancelled is called.
    Then CancellationRequested is raised.
    """
    token = CancellationToken()

    token.cancel()

    with pytest.raises(CancellationRequested):
        token.raise_if_cancelled()


def test_deafult_cancellation_reason():
    """Acceptance scenario.

    Given a new token has no cancellation reason.
    When cancel is called without an explicit reason.
    Then the token records USER_REQUEST.
    """
    token = CancellationToken()

    accepted = token.cancel()

    assert accepted is True

    assert token.reason == CancellationReason.USER_REQUEST


def test_run_timeout_cancellation_reason():
    """Acceptance scenario.

    Given a new token is active.
    When cancel is called with RUN_TIMEOUT.
    Then cancellation is accepted and its reason is RUN_TIMEOUT.
    """
    token = CancellationToken()

    accepted = token.cancel(CancellationReason.RUN_TIMEOUT)

    assert accepted is True

    assert token.reason == CancellationReason.RUN_TIMEOUT


def test_first_cancellation_reason_wins():
    """Acceptance scenario.

    Given USER_REQUEST is the first cancellation.
    When RUN_TIMEOUT is requested afterward.
    Then only the first request is accepted and USER_REQUEST is preserved.
    """
    token = CancellationToken()

    first = token.cancel(CancellationReason.USER_REQUEST)

    second = token.cancel(CancellationReason.RUN_TIMEOUT)

    assert first is True

    assert second is False

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
    assert token.reason == CancellationReason.RUN_TIMEOUT
