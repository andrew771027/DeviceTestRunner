import threading
from enum import Enum


class CancellationReason(str, Enum):
    USER_REQUEST = "user_request"
    RUN_TIMEOUT = "run_timeout"


class CancellationToken:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._reason: CancellationReason | None = None

    def cancel(self, reason: CancellationReason = CancellationReason.USER_REQUEST) -> None:
        """
        Request cancellation.

        Returns:
            True: this call established cancellation.
            False: cancellation was already requested.

        The first cancellation reason wins.
        """
        with self._lock:
            if self._event.is_set():
                return False

            self._reason = reason
            self._event.set()

            return True

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    @property
    def reason(self) -> CancellationReason | None:
        with self._lock:
            return self._reason

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled:
            raise CancellationRequested()


class CancellationRequested(Exception):
    pass
