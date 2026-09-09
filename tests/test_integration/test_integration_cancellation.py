import threading
import time
from pathlib import Path

from runner.artifact import ArtifactManager
from runner.cancellation import CancellationToken
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.models import FailureType, LifecycleStepContent

PROJECT_ROOT = Path(__file__).resolve().parent


def test_executor_cancels_running_process(tmp_path: Path):

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory("cancel_test")

    writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage="scenario",
        step_name="long_running",
        attempt=1,
        show_console=False,
    )

    token = CancellationToken()

    step = LifecycleStepContent(
        name="long_running",
        type="command",
        command=("echo started; " "sleep 10; " "echo finished"),
        timeout_second=30,
    )

    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT, failure_classifier=FailureClassifier()
    )

    def cancel_soon():
        time.sleep(0.2)
        token.cancel()

    cancellation_thread = threading.Thread(target=cancel_soon)

    cancellation_thread.start()

    with writer:

        result = executor.execute(
            step=step,
            stage="scenario",
            attempt=1,
            log_writer=writer,
            working_directory=run_dir,
            cancellation_token=token,
        )

    cancellation_thread.join()

    assert result.success is False
    assert result.cancelled is True
    assert result.timed_out is False
    assert result.failure_type == FailureType.CANCELLED
    assert "started" in result.stdout
