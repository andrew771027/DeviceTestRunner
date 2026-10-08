from dataclasses import dataclass

from runner.cancellation import (
    CancellationReason,
    CancellationToken,
)
from runner.watchdog import CancellationWatchdog


class CleanupTimeoutWatchdog(CancellationWatchdog):

    def __init__(
        self,
        timeout_seconds: float,
        cancellation_token: CancellationToken,
    ) -> None:

        super().__init__(
            timeout_seconds=timeout_seconds,
            cancellation_token=cancellation_token,
            cancellation_reason=CancellationReason.CLEANUP_TIMEOUT,
        )


@dataclass
class CleanupScope:
    cancellation_token: CancellationToken
    watchdog: CleanupTimeoutWatchdog | None = None

    @classmethod
    def create(cls, timeout_seconds: float | None) -> "CleanupScope":

        token = CancellationToken()

        watchdog = None

        if timeout_seconds is not None:
            watchdog = CleanupTimeoutWatchdog(
                timeout_seconds=timeout_seconds,
                cancellation_token=token,
            )

        return cls(
            cancellation_token=token,
            watchdog=watchdog,
        )

    def start(self) -> None:
        if self.watchdog is not None:
            self.watchdog.start()

    def stop(self) -> None:
        if self.watchdog is not None:
            self.watchdog.stop()
