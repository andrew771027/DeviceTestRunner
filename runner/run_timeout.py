from runner.cancellation import (
    CancellationReason,
    CancellationToken,
)
from runner.watchdog import CancellationWatchdog


class RunTimeoutWatchdog(CancellationWatchdog):
    def __init__(
        self,
        timeout_seconds: float,
        cancellation_token: CancellationToken,
    ) -> None:

        super().__init__(
            timeout_seconds=timeout_seconds,
            cancellation_token=cancellation_token,
            cancellation_reason=CancellationReason.RUN_TIMEOUT,
        )
