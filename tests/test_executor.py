import subprocess
import sys
from io import StringIO
from unittest.mock import Mock

import pytest

from runner.artifact import ArtifactManager
from runner.executor import SubprocessExecutor
from runner.models import LifecycleStepContent


@pytest.mark.parametrize(
    argnames="test_case_id, step, stage",
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
            ),
        ]
    ),
)
def test_subprocess_executor_return_success(tmp_path, test_case_id, step, stage):
    executor = SubprocessExecutor()

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir, stage=stage, step_name=step.name, show_console=False
    )

    with log_writer:
        result = executor.execute(step=step, stage=stage, log_writer=log_writer)

    assert result.stage == "test_stage"
    assert result.name == "test"
    assert result.command == "echo 'Hello World'"
    assert result.exit_code == 0
    assert result.passed is True
    assert result.success is True

    assert log_writer.stdout_path.read_text(encoding="utf-8") == result.stdout
    assert result.stdout == "Hello World\n"

    assert log_writer.stderr_path.read_text(encoding="utf-8") == result.stderr
    assert result.stderr == ""


@pytest.mark.parametrize(
    argnames="test_case_id, step, stage",
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
        ),
    ],
)
def test_subprocess_executor_failure(tmp_path, test_case_id, step, stage):
    executor = SubprocessExecutor()

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir, stage=stage, step_name=step.name, show_console=False
    )

    with log_writer:
        result = executor.execute(step=step, stage=stage, log_writer=log_writer)

    assert result.stage == "test_stage"
    assert result.name == "test failed"
    assert result.command == f'{sys.executable} -c "import sys; sys.exit(1)"'
    assert result.exit_code == 1
    assert result.success is False
    assert result.passed is False

    assert log_writer.stdout_path.read_text(encoding="utf-8") == result.stdout
    assert result.stdout == ""

    assert log_writer.stderr_path.read_text(encoding="utf-8") == result.stderr
    assert result.stderr == ""


@pytest.mark.parametrize(
    argnames="tase_case_id, step, stage",
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
        )
    ],
)
def test_subprocess_executor_passes_timeout_to_subprocess(
    tmp_path, monkeypatch, tase_case_id, step, stage
):
    mocked_process = Mock()

    mocked_process.stdout = StringIO("Hello World\n")
    mocked_process.stderr = StringIO("")
    mocked_process.wait.return_value = 0
    mocked_process.returncode = 0

    mocked_popen = Mock(return_value=mocked_process)

    monkeypatch.setattr("runner.executor.subprocess.Popen", mocked_popen)

    executor = SubprocessExecutor()

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=tase_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir, stage=stage, step_name=step.name, show_console=False
    )

    with log_writer:
        result = executor.execute(step=step, stage=stage, log_writer=log_writer)

    mocked_popen.assert_called_once_with(
        step.command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    mocked_process.wait.assert_called_once_with(timeout=5)

    assert result.exit_code == 0
    assert result.stdout == "Hello World\n"
    assert result.stderr == ""

    assert log_writer.stdout_path.read_text(encoding="utf-8") == "Hello World\n"
    assert log_writer.stderr_path.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    argnames="test_case_id, step, stage",
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
        )
    ],
)
def test_subprocess_executor_raised_timeout_error(tmp_path, monkeypatch, test_case_id, step, stage):

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
        run_dir=run_dir, stage=stage, step_name=step.name, show_console=False
    )

    executor = SubprocessExecutor()

    with log_writer:
        result = executor.execute(step=step, stage=stage, log_writer=log_writer)

    mocked_popen.assert_called_once()

    assert result.name == "slow_step"
    assert result.command == "slow command"
    assert result.success is False
    assert result.exit_code is None
    assert result.passed is False

    assert log_writer.stdout_path.read_text(encoding="utf-8") == result.stdout
    assert result.stderr == ""
    assert log_writer.stderr_path.read_text(encoding="utf-8") == result.stderr
    assert result.stdout == ""

    assert result.error == f"Timeout after {step.timeout_second} seconds"
