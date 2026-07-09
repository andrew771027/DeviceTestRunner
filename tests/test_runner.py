import pytest

from runner.models import ArtifactConfig, ScenarioConfig, TestConfig, TestResult
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner


class MockExecutor:
    def run(self, test_name: str, scenario: ScenarioConfig) -> TestResult:
        return TestResult(
            test_name=test_name,
            command=scenario.command,
            success=True,
            exit_code=0,
            duration=0,
            stdout="ok",
            stderr="",
        )


@pytest.mark.parametrize(
    argnames="test_name, scenario, artifact",
    argvalues=[
        (
            "sample_scenario",
            ScenarioConfig(command="echo 1", timeout_second=1),
            ArtifactConfig(output_dir="./"),
        ),
    ],
)
def test_runner_runs_single_scenario(test_name, scenario, artifact):
    config = TestConfig(test_name=test_name, scenario=scenario, artifact=artifact)
    runner = DeviceTestRunner(executor=MockExecutor(), reporter=JsonReporter())
    result = runner.run(config)

    assert result.test_name == test_name
    assert result.command == scenario.command
    assert result.success is True
    assert result.stdout == "ok"
    assert result.stderr == ""
    assert result.exit_code == 0
