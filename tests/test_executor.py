import subprocess
import sys
from unittest.mock import Mock

import pytest

from runner.executor import SubprocessExecutor
from runner.models import LifecycleStepContent


@pytest.mark.parametrize(
    argnames="step, stage",
    argvalues=([
        (
            LifecycleStepContent(
                name="test",
                type="command",
                command="echo 'Hello World'",
                timeout_second=1,
            ),
            "test_stage",
        ),
    ]),
)
def test_subprocess_executor_return_success(step, stage):
    executor = SubprocessExecutor()

    result = executor.execute(step=step, stage=stage)

    assert result.stage == "test_stage"
    assert result.name == "test"
    assert result.command == "echo 'Hello World'"
    assert result.exit_code == 0
    assert result.passed is True
    assert result.success is True
    assert "Hello" in result.stdout
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
def test_subprocess_executor_failure(step, stage):
    executor = SubprocessExecutor()

    result = executor.execute(step=step, stage=stage)

    assert result.stage == "test_stage"
    assert result.name == "test failed"
    assert result.command == f'{sys.executable} -c "import sys; sys.exit(1)"'
    assert result.exit_code == 1
    assert result.success is False
    assert result.passed is False
    assert result.stderr == ""
    assert result.stdout == ""


@pytest.mark.parametrize(argnames="step, stage", 
                         argvalues=[
                            (
                                LifecycleStepContent(
                                    name="timeout_test", 
                                    type="command", 
                                    command="echo 'Hello'", 
                                    timeout_second=5),
                                "test_stage"
                            )
                        ]
                    )
def test_subprocess_executor_passes_timeout_to_subprocess(monkeypatch, step, stage):
    completed_process = subprocess.CompletedProcess(
        args="echo 'Hello World'", returncode=0, stdout="Hello World\n", stderr=""
    )

    mocked_run = Mock(return_value=completed_process)

    monkeypatch.setattr(subprocess, "run", mocked_run)

    executor = SubprocessExecutor()

    result = executor.execute(step=step, stage=stage)

    mocked_run.assert_called_once_with(
        "echo 'Hello'", shell=True, capture_output=True, text=True, timeout=5
    )

    assert result.exit_code == 0

@pytest.mark.parametrize(argnames="step, stage", 
                         argvalues=[
                            (
                                LifecycleStepContent(
                                        name="slow_step",
                                        type="command",
                                        command="slow command",
                                        timeout_second=5,
                                ),
                                "test_stage"
                            )
                    ]
                )
def test_subprocess_executor_raised_timeout_error(monkeypatch, step, stage):
    def raised_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=kwargs.get("args", "slow command"),
            timeout=5,
        )

    monkeypatch.setattr(subprocess, "run", raised_timeout)

    executor = SubprocessExecutor()

    result = SubprocessExecutor().execute(step=step, stage=stage)

    assert result.name == "slow_step"
    assert result.command == "slow command"
    assert result.success is False
    assert result.exit_code is None
    assert result.passed is False
    assert result.stderr == ""
    assert result.stdout == ""
    assert result.error == "Timeout after 5 seconds"
