import threading
import time

from runner.cancellation import CancellationReason, CancellationToken


class RunTimeoutWatchdog:
    def __init__(self, timeout_seconds: float, cancellation_token: CancellationToken) -> None:

        if timeout_seconds <= 0:
            raise ValueError("run_timeout_seconds must be > 0")

        self.timeout_seconds = timeout_seconds
        self.cancellation_token = cancellation_token

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._started_at: float | None = None
        self._deadline: float | None = None

    @property
    def deadline(self) -> float | None:
        return self._deadline

    @property
    def started_at(self) -> float | None:
        return self._started_at

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("RunTimeoutWatchdog can only start once")

        self._started_at = time.monotonic()

        self._deadline = self._started_at + self.timeout_seconds

        self._thread = threading.Thread(
            target=self._watch, name="run-timeout-watchdog", daemon=True
        )

        self._thread.start()

    def _watch(self) -> None:
        assert self._deadline is not None

        while True:

            remaining = self._deadline - time.monotonic()

            if remaining <= 0:

                if not self._stop_event.is_set():

                    self.cancellation_token.cancel(CancellationReason.RUN_TIMEOUT)

                return

            stopped = self._stop_event.eait(timeout=remaining)

            if stopped:
                return

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread is not None:

            self._thread.join()
