import subprocess
import time

from runner.models import LifecycleStep, StepResult


class SubprocessExecutor:

    def execute(self, step: LifecycleStep, stage: str) -> StepResult:

        start_time = time.perf_counter()
        # completed = None

        try:

            completed = subprocess.run(
                step.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=step.timeout_second,
            )

            duration_seconds = time.perf_counter() - start_time

            return StepResult(
                stage=stage,
                name=step.name,
                command=step.command,
                success=completed.returncode == 0,
                exit_code=completed.returncode,
                duration_seconds=duration_seconds,
                stdout=completed.stdout,
                stderr=completed.stderr,
                error="",
            )

        except subprocess.TimeoutExpired as error:

            duration_seconds = time.perf_counter() - start_time

            stdout = error.stdout or ""

            stderr = error.stderr or ""

            return StepResult(
                stage=stage,
                name=step.name,
                command=step.command,
                success=False,
                exit_code=None,
                duration_seconds=duration_seconds,
                stdout=self._normalize_output(stdout),
                stderr=self._normalize_output(stderr),
                error=f"Timeout after {step.timeout_second} seconds",
            )

        except OSError as error:
            duration_seconds = time.perf_counter() - start_time

            return StepResult(
                stage=stage,
                name=step.name,
                command=step.command,
                success=False,
                exit_code=None,
                duration_seconds=duration_seconds,
                stdout="",
                stderr="",
                error=f"Unable to execute command: {error}",
            )

    @staticmethod
    def _normalize_output(
        output: str | bytes | None,
    ) -> str:
        if output is None:
            return ""

        if isinstance(output, bytes):
            return output.decode(
                "utf-8",
                errors="replace",
            )
        return output
