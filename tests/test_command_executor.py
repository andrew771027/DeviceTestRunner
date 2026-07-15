import pytest

from runner.executor import SubprocessExecutor
from runner.models import WorkflowStep


@pytest.mark.parametrize(
    argnames="step",
    argvalues=[
        (
            WorkflowStep(
                name="test",
                type="command",
                command="echo Hello World",
                timeout_second=1,
            )
        ),
    ],
)
def test_command_step_executor_success(step):
    executor = SubprocessExecutor()

    result = executor.execute(step)

    assert result.name == "test"
    assert result.command == "echo Hello World"
    assert result.success is True
    assert "Hello" in result.stdout
    assert result.stderr == ""


@pytest.mark.xfail()
@pytest.mark.parametrize(
    argnames="step",
    argvalues=[
        (
            WorkflowStep(
                name="test failed",
                type="command",
                command="exit 1",
                timeout_second=1,
            )
        ),
    ],
)
def test_command_step_executor_failure(step):
    executor = SubprocessExecutor()

    result = executor.execute(step)

    assert result.name == "test failed"
    assert result.command == "exit 1"
    assert result.success is True
