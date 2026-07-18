import pytest

from runner.models import (
    ArtifactConfig,
    DeviceInfo,
    DeviceTestCase,
    RunnerConfig,
    StepResult,
    Workflow,
    WorkflowStep,
)
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner


def build_success_runner_config() -> RunnerConfig:
    return RunnerConfig(
        test_case=DeviceTestCase(
            id="power_001",
            name="Youtube Playback Power Test (Success)",
            description=("Measure power behavior during " "Youtube playback"),
        ),
        device=DeviceInfo(
            serial="emulator-5566",
            product="pixel",
            build="test_build",
        ),
        workflow=Workflow(
            steps=[
                WorkflowStep(
                    name="setup_device",
                    type="command",
                    command="echo setup",
                    timeout_second=10,
                ),
                WorkflowStep(
                    name="run_scenario",
                    type="command",
                    command="echo scenario",
                    timeout_second=30,
                ),
            ]
        ),
        artifact=ArtifactConfig(
            output_dir="artifact/sample_device_config",
        ),
    )


def build_failure_runner_config() -> RunnerConfig:
    return RunnerConfig(
        test_case=DeviceTestCase(
            id="power_001",
            name="Youtube Playback Power Test (Failed)",
            description=("Measure power behavior during " "Youtube playback"),
        ),
        device=DeviceInfo(
            serial="emulator-5566",
            product="pixel",
            build="test_build",
        ),
        workflow=Workflow(
            steps=[
                WorkflowStep(
                    name="setup_device",
                    type="command",
                    command="echo setup",
                    timeout_second=10,
                ),
                WorkflowStep(
                    name="run_failed_scenario",
                    type="command",
                    command="exit 1",
                    timeout_second=30,
                ),
                WorkflowStep(
                    name="run_scenario",
                    type="command",
                    command="echo Hello World",
                    timeout_second=5,
                ),
            ]
        ),
        artifact=ArtifactConfig(
            output_dir="artifact/sample_device_config",
        ),
    )


class MockSuccessExecutor:
    def __init__(self):
        self.executed_steps = []

    def execute(self, step: WorkflowStep) -> StepResult:
        self.executed_steps.append(step.name)

        return StepResult(
            step_name=step.name,
            command=step.command,
            success=True,
            exit_code=0,
            duration_seconds=0,
            stdout="ok",
            stderr="",
        )


@pytest.mark.parametrize(
    argnames="config",
    argvalues=[build_success_runner_config()],
)
def test_runner_executes_all_steps_when_success(config):
    executor = MockSuccessExecutor()
    runner = DeviceTestRunner(executor=executor, reporter=JsonReporter())
    result = runner.run(config)

    assert result.metadata.test_case_name == "Youtube Playback Power Test (Success)"
    assert result.passed is True
    assert len(result.step_results) == 2
    assert executor.executed_steps == ["setup_device", "run_scenario"]


class MockFailedExecutor:
    def __init__(self):
        self.executed_steps = []

    def execute(self, step: WorkflowStep) -> StepResult:
        self.executed_steps.append(step.name)

        if step.name == "run_failed_scenario":
            return StepResult(
                step_name=step.name,
                command=step.command,
                success=False,
                exit_code=1,
                duration_seconds=2,
                stdout="",
                stderr="failed",
            )

        return StepResult(
            step_name=step.name,
            command=step.command,
            success=True,
            exit_code=0,
            duration_seconds=2,
            stdout="ok",
            stderr="",
        )


@pytest.mark.parametrize(
    argnames="config",
    argvalues=[build_failure_runner_config()],
)
def test_runner_terminate_when_step_failed(config):
    executor = MockFailedExecutor()
    runner = DeviceTestRunner(executor=executor, reporter=JsonReporter())
    result = runner.run(config)

    assert result.metadata.test_case_name == "Youtube Playback Power Test (Failed)"
    assert result.passed is False
    assert len(result.step_results) == 2
    assert executor.executed_steps == ["setup_device", "run_failed_scenario"]

    assert result.step_results[0].exit_code == 0
    assert result.step_results[1].exit_code == 1
