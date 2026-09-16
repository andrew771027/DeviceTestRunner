import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, TextIO

from runner.artifact import StepLogWriter
from runner.cancellation import CancellationToken
from runner.failure import FailureClassifier
from runner.models import FailureType, LifecycleStepContent, StepAttemptResult
from runner.process import ProcessTerminator

class SubprocessExecutor:
    POLL_INTERVAL_SECONDS = 0.1

    def __init__(
        self,
        project_directory: str | Path,
        failure_classifier: FailureClassifier,
        process_terminator: ProcessTerminator,
    ):
        self.project_directory = Path(project_directory).resolve()
        self.failure_classifier = failure_classifier
        self.process_terminator = process_terminator

    def execute(
        self,
        step: LifecycleStepContent,
        stage: str,
        attempt: int,
        log_writer: StepLogWriter | None,
        working_directory: str | Path,
        cancellation_token: CancellationToken,
    ) -> StepAttemptResult:

        if log_writer is None:
            log_writer = self._create_default_log_writer(stage=stage, step_name=step.name)

        environment = os.environ.copy()

        environment["DEVICE_TEST_RUNNER_ROOT"] = str(self.project_directory)

        environment["RUN_ARTIFACT_DIR"] = str(Path(working_directory).resolve())

        start_time = time.perf_counter()

        process: subprocess.Popen[str] | None = None

        stdout_thread: threading.Thread | None = None
        stderr_thread: threading.Thread | None = None

        timed_out: bool = False
        cancelled: bool = False

        error_message: str | None = None

        try:
            #
            # ----------------------------------------------
            # Start process group
            # ----------------------------------------------
            #

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

                # 
                # Important:
                # this attempt gets its own session / 
                # process group
                start_new_session=True
            )

            if process.stdout is None or process.stderr is None:
                raise RuntimeError("Unable to open subprocess streams.")

            # 
            # --------------------------------------------
            # stdout reader
            # --------------------------------------------
            #

            stdout_thread = threading.Thread(
                target=self._consume_stream,
                args=(process.stdout, log_writer.write_stdout),
                name=f"{stage}-{step.name}-stdout",
                daemon=True,
            )

            # 
            # --------------------------------------------
            # stderr reader
            # --------------------------------------------
            #

            stderr_thread = threading.Thread(
                target=self._consume_stream,
                args=(process.stderr, log_writer.write_stderr),
                name=f"{stage}-{step.name}-stderr",
                daemon=True,
            )

            stdout_thread.start()
            stderr_thread.start()

            #
            # --------------------------------------------
            # Process monitoring loop
            # --------------------------------------------
            #

            while True:

                # 
                # 1. process 已經正常結束
                #
                if process.poll() is not None:
                    break
                #
                # 2. 外部要求取消
                #
                if cancellation_token.is_cancelled:
                    cancelled = True

                    error_message = "Execution cancelled"

                    self._stop_process(process)

                    break

                #
                # 3. timeout
                #
                elapsed_seconds = time.perf_counter() - start_time

                if elapsed_seconds >= step.timeout_second:
                    timed_out = True

                    error_message = f"Command timeout after {step.timeout_second}"

                    self.process_terminator.terminate_process_group(process)

                    break

                time.sleep(self.POLL_INTERVAL_SECONDS)

            #
            # -----------------------------------------
            # Make sure direct child has been reaped
            # -----------------------------------------
            #

            if process.poll() is None:
                process.wait()

            #
            # ----------------------------------------
            # Drain stdout/stderr
            # ----------------------------------------
            #

            self._join_reader_thread(stdout_thread)

            self._join_reader_thread(stderr_thread)

            duration_seconds = time.perf_counter() - start_time

            #
            # ---------------------------------------
            # Classifiaction
            # ---------------------------------------
            #

            if cancelled:

                success = False

                failure_type = FailureType.CANCELLED

            else:

                success = not timed_out and process.returncode == 0

                failure_type = self.failure_classifier.classify_process_failure(
                    process_success=success,
                    timed_out=timed_out,
                    stderr=log_writer.stderr,
                    error=error_message,
                )

            return StepAttemptResult(
                attempt=attempt,
                success=success,
                failure_type=failure_type,
                timed_out=timed_out,
                cancelled=cancelled,
                exit_code=process.returncode,
                duration_seconds=duration_seconds,
                stdout=log_writer.stdout,
                stderr=log_writer.stderr,
                stdout_log_path=str(log_writer.stdout_path),
                stderr_log_path=str(log_writer.stderr_path),
                error=error_message,
                artifact_validation_results=[],
            )

        except (OSError, RuntimeError) as error:
            duration_seconds = time.perf_counter() - start_time
            error_message = f"Unable to execute command: {error}"

            log_writer.write_stderr(f"{error_message}\n")

            #
            # Exception 發生時也不能留下 process
            #

            if process is not None and process.poll() is None:
                self.process_terminator.terminate_process_group(process)

            self._join_reader_thread(stdout_thread)

            self._join_reader_thread(stderr_thread)

            return StepAttemptResult(
                attempt=attempt,
                success=False,
                failure_type=FailureType.PROCESS_ERROR,
                timed_out=False,
                cancelled=False,
                exit_code=process.returncode if process is not None else None,
                duration_seconds=duration_seconds,
                stdout=log_writer.stdout,
                stderr=log_writer.stderr,
                stdout_log_path=str(log_writer.stdout_path),
                stderr_log_path=str(log_writer.stderr_path),
                error=error_message,
                artifact_validation_results=[],
            )


    @staticmethod
    def _consume_stream(stream: TextIO, write_line) -> None:
        try:
            for line in iter(stream.readline, ""):
                write_line(line)
        finally:
            stream.close()

    @staticmethod
    def _join_reader_thread(thread: threading.Thread | None) -> None:
        if thread is None:
            return

        thread.join(timeout=2)

        if thread.is_alive():
            raise RuntimeError("Output reader thread did not stop.")

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
