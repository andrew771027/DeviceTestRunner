from pathlib import Path

from runner.artifact import ArtifactManager
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.models import FailureType, LifecycleStepContent


def test_executor_classifies_timeout(tmp_path: Path):
    artifat_manager = ArtifactManager(output_dir=tmp_path)

    run_dir = artifat_manager.create_run_directory("timeout_test")

    writer = artifat_manager.create_step_log_writer(
        run_dir=run_dir,
        stage="scenario",
        step_name="timeout",
        attempt=1,
        show_console=False,
    )

    step = LifecycleStepContent(name="timeout", type="command", command="sleep 5", timeout_second=1)

    executor = SubprocessExecutor(
        project_directory=tmp_path,
        failure_classifier=FailureClassifier(),
    )

    with writer:
        result = executor.execute(
            step=step,
            stage="scenario",
            attempt=1,
            log_writer=writer,
            working_directory=run_dir,
        )

    assert result.success is False
    assert result.failure_type == FailureType.TIMEOUT


def test_executor_classifies_device_offline(tmp_path: Path):
    artifact_manager = ArtifactManager(output_dir=tmp_path)

    run_dir = artifact_manager.create_run_directory("offline_test")

    writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage="scenario",
        step_name="adb",
        attempt=1,
        show_console=False,
    )

    step = LifecycleStepContent(
        name="adb",
        type="command",
        command=("sh -c " '\'echo "error: device offline" ' ">&2; exit 1'"),
        timeout_second=5,
    )

    executor = SubprocessExecutor(
        project_directory=tmp_path,
        failure_classifier=FailureClassifier(),
    )

    with writer:
        result = executor.execute(
            step=step,
            stage="scenario",
            attempt=1,
            log_writer=writer,
            working_directory=run_dir,
        )

    assert result.success is False
    assert result.failure_type == FailureType.DEVICE_OFFLINE


def test_executor_classifies_process_error(tmp_path: Path):
    artifact_manager = ArtifactManager(output_dir=tmp_path)

    run_dir = artifact_manager.create_run_directory("process_test")

    writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage="failure",
        step_name="process_test",
        attempt=1,
        show_console=False,
    )

    step = LifecycleStepContent(
        name="failure",
        type="command",
        command=("sh -c " "'echo failed >&2; exit 42'"),
        timeout_second=5,
    )

    executor = SubprocessExecutor(
        project_directory=tmp_path,
        failure_classifier=FailureClassifier(),
    )

    with writer:
        result = executor.execute(
            step=step,
            stage="scenario",
            attempt=1,
            log_writer=writer,
            working_directory=run_dir,
        )

    assert result.success is False
    assert result.exit_code == 42
    assert result.failure_type == FailureType.PROCESS_ERROR
