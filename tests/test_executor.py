import subprocess
import sys
from unittest.mock import Mock

import pytest

from runner.executor import SubprocessExecutor
from runner.models import LifecycleStepContent
from runner.artifact import ArtifactManager

@pytest.mark.parametrize(
    argnames="step, stage",
    argvalues=(
        [
            (
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
def test_subprocess_executor_return_success(tmp_path, step, stage):
    executor = SubprocessExecutor()

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id="test_case_001")

    log_writer = artifact_manager.create_step_log_writer(run_dir=run_dir, stage=stage, step_name=step.name, show_console=False)

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
    argnames="step, stage",
    argvalues=[
        (
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
def test_subprocess_executor_failure(tmp_path, step, stage):
    executor = SubprocessExecutor()

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id="test_case_001")

    log_writer = artifact_manager.create_step_log_writer(run_dir=run_dir, stage=stage, step_name=step.name, show_console=False)

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
    argnames="step, stage",
    argvalues=[
        (
            LifecycleStepContent(
                name="timeout_test",
                type="command",
                command="echo 'Hello'",
                timeout_second=5,
            ),
            "test_stage",
        )
    ],
)
def test_subprocess_executor_passes_timeout_to_subprocess(tmp_path, monkeypatch, step, stage):
    mock_process = Mock()
    
    mock_process.communicate.return_value = ("Hello World\n", "")

    mocked_popen = Mock(return_value=mock_process)

    monkeypatch.setattr(subprocess, "Popen", mocked_popen)

    executor = SubprocessExecutor()

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id="test_case_001")

    log_writer = artifact_manager.create_step_log_writer(run_dir=run_dir, stage=stage, step_name=step.name, show_console=False)

    with log_writer:
        result = executor.execute(step=step, stage=stage, log_writer=log_writer)

    mocked_popen.assert_called_once_with(
        "echo 'Hello'", 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True
    )

    mocked_process.communicate.assert_called_once_with(timeout=15)

    assert result.exit_code == 0


@pytest.mark.parametrize(
    argnames="step, stage",
    argvalues=[
        (
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
def test_subprocess_executor_raised_timeout_error(tmp_path, monkeypatch, step, stage):
    def raised_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=kwargs.get("args", "slow command"),
            timeout=5,
        )

    monkeypatch.setattr(subprocess, "run", raised_timeout)

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id="test_case_001")

    log_writer = artifact_manager.create_step_log_writer(run_dir=run_dir, stage=stage, step_name=step.name, show_console=False)

    executor = SubprocessExecutor()

    with log_writer:
        result = executor.execute(step=step, stage=stage, log_writer=log_writer)

    assert result.name == "slow_step"
    assert result.command == "slow command"
    assert result.success is False
    assert result.exit_code is None
    assert result.passed is False
    
    assert log_writer.stdout_path.read_text(encoding="utf-8") == result.stdout
    assert result.stderr == ""
    assert log_writer.stderr_path.read_text(encoding="utf-8") == result.stderr
    assert result.stdout == ""

    assert result.error == "Timeout after 5 seconds"
