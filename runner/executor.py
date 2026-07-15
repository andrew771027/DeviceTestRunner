import subprocess
import time

from runner.models import StepResult, WorkflowStep


class SubprocessExecutor:

    def execute(self, step: WorkflowStep) -> StepResult:

        start_time = time.time()

        try:

            completed = subprocess.run(
                step.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=step.timeout_second,
            )

            duration_seconds = time.time() - start_time

            return StepResult(
                step_name=step.name,
                command=step.command,
                success=completed.returncode == 0,
                exit_code=completed.returncode,
                duration_seconds=duration_seconds,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )

        except subprocess.TimeoutExpired as e:

            duration_seconds = time.time() - start_time

            stdout = e.stdout or ""
            stderr = e.stderr or ""

            if isinstance(stdout, bytes):
                stdout = stdout.decode(encoding="utf-8", error="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode(encoding="utf-8", error="repalce")

            return StepResult(
                step_name=step.name,
                command=step.command,
                success=False,
                exit_code=completed.returncode,
                duration_seconds=duration_seconds,
                stdout=stdout,
                strerr=stderr,
                error=f"Timeout after {step.timeout_second} seconds",
            )
