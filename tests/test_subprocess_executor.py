import pytest

from runner.executor import SubprocessScenarioExecutor
from runner.models import ScenarioConfig


@pytest.mark.parametrize(
    argnames="test_name, scenario",
    argvalues=[
        (
            "echo_test",
            ScenarioConfig(
                command='echo "Hello World"',
                timeout_second=30,
            ),
        ),
    ],
)
def test_subprocess_executor_success(test_name, scenario):
    executor = SubprocessScenarioExecutor()

    result = executor.run(test_name=test_name, scenario=scenario)

    assert result.test_name == "echo_test"
    assert result.command == 'echo "Hello World"'
    assert result.success is True
    assert "Hello" in result.stdout
    assert result.stderr == ""


@pytest.mark.xfail()
@pytest.mark.parametrize(
    argnames="test_name, scenario",
    argvalues=[
        (
            "fail_test",
            ScenarioConfig(
                command="echo 1",
                timeout_second=30,
            ),
        ),
    ],
)
def test_subprocess_executor_failure(test_name, scenario):
    executor = SubprocessScenarioExecutor()

    result = executor.run(test_name=test_name, scenario=scenario)

    assert result.test_name == "fail_test"
    assert result.command == "echo 1"
    assert result.success is True
