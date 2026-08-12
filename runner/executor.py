import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import TextIO

from runner.artifact import StepLogWriter
from runner.models import LifecycleStepContent, StepAttemptResult


class SubprocessExecutor:

    def __init__(
        self,
        project_directory: str | Path,
    ):
        self.project_directory = Path(project_directory).resolve()

    def execute(
        self,
        step: LifecycleStepContent,
        stage: str,
        attempt: int,
        log_writer: StepLogWriter | None,
        working_directory: str | Path,
    ) -> StepAttemptResult:

        if log_writer is None:
            log_writer = self._create_default_log_writer(stage=stage, step_name=step.name)

        environment = os.environ.copy()

        environment["DEVICE_TEST_RUNNER_ROOT"] = str(self.project_directory)

        environment["RUN_ARTIFACT_DIR"] = str(Path(working_directory).resolve())

        start_time = time.perf_counter()
        process: subprocess.Popen[str] | None = None
        error_message: str | None = None
        time_out: bool = False

        try:
            process = subprocess.Popen(
                step.command,
                shell=True,
                cwd=str(working_directory),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )

            if process.stdout is None or process.stderr is None:
                raise RuntimeError("Unable to open subprocess streams.")

            stdout_thread = threading.Thread(
                target=self._consume_stream,
                args=(process.stdout, log_writer.write_stdout),
                name=f"{stage}-{step.name}-stdout",
                daemon=True,
            )

            stderr_thread = threading.Thread(
                target=self._consume_stream,
                args=(process.stderr, log_writer.write_stderr),
                name=f"{stage}-{step.name}-stderr",
                daemon=True,
            )

            stdout_thread.start()
            stderr_thread.start()

            try:
                process.wait(timeout=step.timeout_second)
            except subprocess.TimeoutExpired:
                time_out = True
                error_message = f"Timeout after {step.timeout_second} seconds"
                self._stop_process(process)

            stdout_thread.join()
            stderr_thread.join()

            exit_code = process.returncode
            duration_seconds = time.perf_counter() - start_time
            success = not time_out and exit_code == 0

            return StepAttemptResult(
                attempt=attempt,
                success=success,
                exit_code=exit_code,
                duration_seconds=duration_seconds,
                stdout=log_writer.stdout,
                stderr=log_writer.stderr,
                stdout_log_path=str(log_writer.stdout_path),
                stderr_log_path=str(log_writer.stderr_path),
                error=error_message,
            )

        except OSError as error:
            duration_seconds = time.perf_counter() - start_time
            error_message = f"Unable to execute command: {error}"

            log_writer.write_stderr(f"{error_message}\n")

            return StepAttemptResult(
                attempt=attempt,
                success=False,
                exit_code=None,
                duration_seconds=duration_seconds,
                stdout=log_writer.stdout,
                stderr=log_writer.stderr,
                stdout_log_path=str(log_writer.stdout_path),
                stderr_log_path=str(log_writer.stderr_path),
                error=error_message,
            )

        except RuntimeError as error:
            duration_seconds = time.perf_counter() - start_time
            error_message = str(error)

            log_writer.write_stderr(f"{error_message}\n")

            if process is not None:
                self._stop_process(process)

            return StepAttemptResult(
                attempt=attempt,
                success=False,
                exit_code=process.returncode if process is not None else None,
                duration_seconds=duration_seconds,
                stdout=log_writer.stdout,
                stderr=log_writer.stderr,
                stdout_log_path=str(log_writer.stdout_path),
                stderr_log_path=str(log_writer.stderr_path),
                error=error_message,
            )

    @staticmethod
    def _consume_stream(stream: TextIO, write_line) -> None:
        try:
            for line in iter(stream.readline, ""):
                write_line(line)
        finally:
            stream.close()

    @staticmethod
    def _stop_process(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return

        process.terminate()

        try:
            process.wait()
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    @staticmethod
    def _create_default_log_writer(stage: str, step_name: str) -> StepLogWriter:
        temp_dir = Path(tempfile.mkdtemp(prefix="step-", suffix=".logs"))
        return StepLogWriter(
            stage=stage,
            step_name=step_name,
            stdout_path=temp_dir / f"{step_name}.stdout.log",
            stderr_path=temp_dir / f"{step_name}.stderr.log",
            show_console=False,
        )
