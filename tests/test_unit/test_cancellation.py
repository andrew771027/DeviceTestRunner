import pytest

from runner.cancellation import CancellationRequested, CancellationToken


def test_token_not_cancelled_initially():
    """Acceptance scenario.

    Given a newly constructed cancellation token.
    When its state is read.
    Then is_cancelled is false.
    """
    token = CancellationToken()

    assert token.is_cancelled is False


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
