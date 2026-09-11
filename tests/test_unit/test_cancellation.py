import pytest

from runner.cancellation import CancellationRequested, CancellationToken


def test_token_not_cancelled_initially():
    token = CancellationToken()

    assert token.is_cancelled is False


def test_token_can_be_cancelled():
    token = CancellationToken()

    token.cancel()
    assert token.is_cancelled is True


def test_cancel_is_idempotent():
    token = CancellationToken()

    token.cancel()

    token.cancel()

    assert token.is_cancelled is True


def test_raise_if_cancelled_does_nothing_when_active():
    token = CancellationToken()

    token.raise_if_cancelled()


def test_raise_if_cancelled_raises_after_cancel():
    token = CancellationToken()

    token.cancel()

    with pytest.raises(CancellationRequested):
        token.raise_if_cancelled()
