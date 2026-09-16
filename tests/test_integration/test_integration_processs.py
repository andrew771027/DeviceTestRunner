import os
import subprocess
import time
import threading
from pathlib import Path
from runner.process import ProcessTerminator
from runner.cancellation import CancellationToken
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.models import LifecycleStepContent
from runner.artifact import ArtifactManager

PROJECT_ROOT = Path(__file__).resolve().parent

def test_process_group_termination_cleans_child_processes(tmp_path: Path):

    child_pid_file = tmp_path / "child.pid"

    command = f"""
    sleep 30 &
    CHILD_PID=$!
    echo $CHILD_PID > "{child_pid_file}"
    wait $CHILD_PID
"""

    process = subprocess.Popen(
        command,
        shell=True,
        start_new_session=True,
    )

    #
    # 等child PID 寫出來
    #
    deadline = time.monotonic() + 2

    while not child_pid_file.exists():

        if time.monotonic() >= deadline:
            raise AssertionError(
                "Child PID file was not created"
            )

        time.sleep(0.05)

    child_pid = int(child_pid_file.read_text().strip())

    #
    # Child 一開始應該存在
    # 
    os.kill(child_pid, 0)

    process_terminator = ProcessTerminator(grace_period_seconds=0.5)

    process_terminator.terminate_process_group(process)

    #
    # 給 OS 一點時間完成 process cleanup
    # 
    time.sleep(0.1)

    try:

        os.kill(child_pid, 0)

        child_alive = True

    except ProcessLookupError:

        child_alive = False

    assert child_alive is False


def test_stdout_reader_thread_finishes_after_process_termination(tmp_path: Path):

    token = CancellationToken()

    executor = SubprocessExecutor(
        process_terminator=PROJECT_ROOT,
        failure_classifier=FailureClassifier(),
        process_terminator=ProcessTerminator(grace_period_seconds=0.5)
    )

    step = LifecycleStepContent(
        name="streaming",
        type="command",
        command=(
            "echo start; " \
            "sleep 30"
        ),
        timeout_second=60
    )

    artifat_manager = ArtifactManager(tmp_path)

    run_dir = artifat_manager.create_run_directory("stream_test")

    writer = artifat_manager.create_step_log_writer(run_dir=run_dir,
                                                    stage="scenario",
                                                    step_name="streaming",
                                                    attemp=1,
                                                    show_console=False)

    def cancel_soon():
        time.sleep(0.2)
        token.cancel()

    thread = threading.Thread(target=cancel_soon)

    thread.start()

    with writer:

        result = executor.execute(
            step=step,
            stage="scenario",
            attempt=1,
            log_writer=writer,
            working_directory=run_dir,
            cancellation_token=token
        )

    thread.join()

    assert result.cancelled is True
    assert "start" in result.stdout

def test_stderr_is_drained_after_cancellation(tmp_path: Path):

    token = CancellationToken()
    
    executor = SubprocessExecutor(
        process_terminator=PROJECT_ROOT,
        failure_classifier=FailureClassifier(),
        process_terminator=ProcessTerminator(grace_period_seconds=0.5)
    )

    step = LifecycleStepContent(
        name="stderr_test",
        type="command",
        command=(
            "echo error-message >&2; " \
            "sleep 30"
        ),
        timeout_second=60
    )

    artifat_manager = ArtifactManager(tmp_path)

    run_dir = artifat_manager.create_run_directory("stream_test")

    writer = artifat_manager.create_step_log_writer(run_dir=run_dir,
                                                    stage="scenario",
                                                    step_name="stderr_test",
                                                    attemp=1,
                                                    show_console=False)

    def cancel_soon():
        time.sleep(0.2)
        token.cancel()
    
    thread = threading.Thread(target=cancel_soon)

    thread.start()

    with writer:

        result = executor.execute(
            step=step,
            stage="scenario",
            attempt=1,
            log_writer=writer,
            working_directory=run_dir,
            cancellation_token=token
        )

    thread.join()

    assert result.cancelled is True
    assert "error-message" in result.stderr