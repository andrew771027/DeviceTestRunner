import signal

import pytest

from main import SignalCancellationHandler
from runner.cancellation import CancellationToken


def test_first_sigint_cancels_token():

    """Acceptance scenario.

    Given a signal handler has an active token.
    When its SIGINT handler is called once.
    Then the token is cancelled without interrupting the test.
    """
    token = CancellationToken()
    handler = SignalCancellationHandler(token)

    # 第一次 Ctrl+C：通知 runner 取消，讓它有機會清理 process。
    # 直接呼叫 handler，避免真的把 pytest 中斷。
    handler.handle_sigint(signal.SIGINT, None)

    assert token.is_cancelled is True


def test_second_sigint_raises_keyboard_interrupt():

    """Acceptance scenario.

    Given a signal handler has received its first SIGINT.
    When its SIGINT handler is called again.
    Then KeyboardInterrupt is raised and the token remains cancelled.
    """
    token = CancellationToken()
    handler = SignalCancellationHandler(token)

    # 第一次只發出取消通知。
    handler.handle_sigint(signal.SIGINT, None)

    # 第二次必須拋出 KeyboardInterrupt。
    # pytest.raises 會確認有沒有出現指定的 exception。
    with pytest.raises(KeyboardInterrupt):
        handler.handle_sigint(signal.SIGINT, None)

    # 第二次中斷後，token 仍然維持取消狀態。
    assert token.is_cancelled is True
