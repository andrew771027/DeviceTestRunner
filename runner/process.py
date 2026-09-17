import os
import signal
import subprocess
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessTerminationResult:
    terminated: bool
    killed: bool
    return_code: int | None


class ProcessTerminator:

    def __init__(self, grace_period_seconds: float = 2.0, poll_interval_seconds: float = 0.05):
        if grace_period_seconds < 0:
            raise ValueError("grace_period_seconds must be >= 0")

        if poll_interval_seconds <= 0:
            raise ValueError("poll_internal_seconds must be > 0")

        self.grace_period_seconds = grace_period_seconds
        self.poll_internal_seconds = poll_interval_seconds

    def terminate_process_group(self, process: subprocess.Popen) -> ProcessTerminationResult:

        #
        # Process 已經結束
        #
        if process.poll() is not None:
            return ProcessTerminationResult(
                terminated=False,
                killed=False,
                return_code=process.returncode,
            )

        try:

            process_group_id = os.getpgid(process.pid)

        except ProcessLookupError:
            return ProcessTerminationResult(
                terminated=False,
                killed=False,
                return_code=process.poll(),
            )

        #
        # --------------------------------------------------
        # Phase 1
        # Graceful termination
        # --------------------------------------------------
        #
        try:

            os.killpg(process_group_id, signal.SIGTERM)

        except ProcessLookupError:
            pass

        #
        # 給 process group 一段時間自己 cleanup
        #
        exited = self._wait_for_exit(
            process=process,
            process_group_id=process_group_id,
            timeout_seconds=self.grace_period_seconds,
        )

        if exited:
            return ProcessTerminationResult(
                terminated=True,
                killed=False,
                return_code=process.returncode,
            )

        #
        # ------------------------------------------------
        # Phase 3
        # Force kill
        # ------------------------------------------------
        #
        try:

            os.killpg(process_group_id, signal.SIGKILL)

        except ProcessLookupError:
            pass

        #
        # Reap the direct child and wait for descendants before allowing retry.
        #
        if not self._wait_for_exit(
            process=process, process_group_id=process_group_id, timeout_seconds=2
        ):
            raise RuntimeError("Process group did not exit after SIGKILL.")

        return ProcessTerminationResult(terminated=True, killed=True, return_code=process.poll())

    def _wait_for_exit(
        self, process: subprocess.Popen, process_group_id: int, timeout_seconds: float
    ) -> bool:

        deadline = time.monotonic() + timeout_seconds

        while True:

            # poll() reaps the direct child, but its exit alone says nothing
            # about descendants that may still hold stdout/stderr open.
            process.poll()
            try:
                os.killpg(process_group_id, 0)
            except ProcessLookupError:
                return True
            except PermissionError:
                # Lack of permission does not prove that the group is gone.
                # Retry until it disappears or the bounded wait expires.
                pass

            remaining = deadline - time.monotonic()

            if remaining <= 0:
                return False

            time.sleep(min(self.poll_internal_seconds, remaining))
