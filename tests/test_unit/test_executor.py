import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock

import pytest

from runner.artifact import ArtifactManager
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.models import LifecycleStepContent

PROJECT_ROOT = Path(__file__).resolve().parent


@pytest.mark.parametrize(
    argnames="test_case_id, step, stage, attempt",
    argvalues=(
        [
            (
                "test_case_001",
                LifecycleStepContent(
                    name="test",
                    type="command",
                    command="echo 'Hello World'",
                    timeout_second=1,
                ),
                "test_stage",
                1,
            ),
        ]
    ),
)
def test_subprocess_executor_return_success(tmp_path, test_case_id, step, stage, attempt):
    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT, failure_classifier=FailureClassifier()
    )

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage=stage,
        step_name=step.name,
        attempt=attempt,
        show_console=False,
    )

    with log_writer:
        result = executor.execute(
            step=step,
            stage=stage,
            attempt=attempt,
            log_writer=log_writer,
            working_directory=run_dir,
        )

    assert result.attempt == attempt
    assert result.exit_code == 0
    assert result.passed is True
    assert result.success is True

    assert log_writer.stdout_path.read_text(encoding="utf-8") == result.stdout
    assert result.stdout == "Hello World\n"

    assert log_writer.stderr_path.read_text(encoding="utf-8") == result.stderr
    assert result.stderr == ""


@pytest.mark.parametrize(
    argnames="test_case_id, step, stage, attempt",
    argvalues=[
        (
            "test_case_001",
            LifecycleStepContent(
                name="test failed",
                type="command",
                command=f'{sys.executable} -c "import sys; sys.exit(1)"',
                timeout_second=1,
            ),
            "test_stage",
            1,
        ),
    ],
)
def test_subprocess_executor_failure(tmp_path, test_case_id, step, stage, attempt):
    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT, failure_classifier=FailureClassifier()
    )

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage=stage,
        step_name=step.name,
        attempt=attempt,
        show_console=False,
    )

    with log_writer:
        result = executor.execute(
            step=step,
            stage=stage,
            attempt=attempt,
            log_writer=log_writer,
            working_directory=run_dir,
        )

    assert result.attempt == attempt
    assert result.exit_code == 1
    assert result.success is False
    assert result.passed is False

    assert log_writer.stdout_path.read_text(encoding="utf-8") == result.stdout
    assert result.stdout == ""

    assert log_writer.stderr_path.read_text(encoding="utf-8") == result.stderr
    assert result.stderr == ""


@pytest.mark.parametrize(
    argnames="tase_case_id, step, stage, attempt",
    argvalues=[
        (
            "test_case_001",
            LifecycleStepContent(
                name="timeout_test",
                type="command",
                command="echo 'Hello World'",
                timeout_second=5,
            ),
            "test_stage",
            1,
        )
    ],
)
def test_subprocess_executor_passes_timeout_to_subprocess(
    tmp_path, monkeypatch, tase_case_id, step, stage, attempt
):
    mocked_process = Mock()

    mocked_process.stdout = StringIO("Hello World\n")
    mocked_process.stderr = StringIO("")
    mocked_process.wait.return_value = 0
    mocked_process.returncode = 0

    mocked_popen = Mock(return_value=mocked_process)

    monkeypatch.setattr("runner.executor.subprocess.Popen", mocked_popen)

    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT, failure_classifier=FailureClassifier()
    )

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=tase_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage=stage,
        step_name=step.name,
        attempt=attempt,
        show_console=False,
    )

    with log_writer:
        result = executor.execute(
            step=step,
            stage=stage,
            attempt=attempt,
            log_writer=log_writer,
            working_directory=run_dir,
        )

    mocked_popen.assert_called_once()
    args, kwargs = mocked_popen.call_args

    assert args == (step.command,)
    assert kwargs["shell"] is True
    assert kwargs["cwd"] == str(run_dir)
    assert kwargs["env"]["DEVICE_TEST_RUNNER_ROOT"] == str(PROJECT_ROOT.resolve())
    assert kwargs["env"]["RUN_ARTIFACT_DIR"] == str(run_dir.resolve())
    assert kwargs["stdout"] == subprocess.PIPE
    assert kwargs["stderr"] == subprocess.PIPE
    assert kwargs["text"] is True
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["errors"] == "replace"
    assert kwargs["bufsize"] == 1

    mocked_process.wait.assert_called_once_with(timeout=5)

    assert result.exit_code == 0
    assert result.stdout == "Hello World\n"
    assert result.stderr == ""

    assert log_writer.stdout_path.read_text(encoding="utf-8") == "Hello World\n"
    assert log_writer.stderr_path.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    argnames="test_case_id, step, stage, attempt",
    argvalues=[
        (
            "test_case_001",
            LifecycleStepContent(
                name="slow_step",
                type="command",
                command="slow command",
                timeout_second=5,
            ),
            "test_stage",
            1,
        )
    ],
)
def test_subprocess_executor_raised_timeout_error(
    tmp_path, monkeypatch, test_case_id, step, stage, attempt
):

    mocked_process = Mock()

    # Reader threads 會讀取這兩個 stream。
    mocked_process.stdout = StringIO("")
    mocked_process.stderr = StringIO("")

    # timeout 應發生在 wait()，不是 Popen()。
    mocked_process.wait.side_effect = subprocess.TimeoutExpired(
        cmd=step.command,
        timeout=step.timeout_second,
    )

    mocked_process.returncode = None

    mocked_popen = Mock(return_value=mocked_process)

    monkeypatch.setattr("runner.executor.subprocess.Popen", mocked_popen)

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage=stage,
        step_name=step.name,
        attempt=attempt,
        show_console=False,
    )

    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT, failure_classifier=FailureClassifier()
    )

    with log_writer:
        result = executor.execute(
            step=step,
            stage=stage,
            attempt=attempt,
            log_writer=log_writer,
            working_directory=run_dir,
        )

    mocked_popen.assert_called_once()

    assert result.attempt == 1
    assert result.success is False
    assert result.exit_code is None
    assert result.passed is False

    assert log_writer.stdout_path.read_text(encoding="utf-8") == result.stdout
    assert result.stderr == ""
    assert log_writer.stderr_path.read_text(encoding="utf-8") == result.stderr
    assert result.stdout == ""

    assert result.error == f"Timeout after {step.timeout_second} seconds"
