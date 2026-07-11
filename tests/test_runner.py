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


class MockSuccessExecutor:
    def __init__(self):
        self.executed_steps = []

    def execute(self, step: WorkflowStep) -> StepResult:
        self.executed_steps.append(step.name)

        return StepResult(
            name=step.name,
            command=step.command,
            success=True,
            exit_code=0,
            duration_seconds=0,
            stdout="ok",
            stderr="",
        )


@pytest.mark.parametrize(
    argnames="config",
    argvalues=[
        RunnerConfig(
            test_case=DeviceTestCase(id="001", name="success_runner", description="success"),
            device=DeviceInfo(serial="0000000000", product="faker_product", build="123456"),
            workflow=Workflow(
                steps=[
                    WorkflowStep(
                        name="1st step",
                        type="command",
                        command="echo Hello World",
                        timeout_second=1,
                    ),
                    WorkflowStep(
                        name="2nd step",
                        type="command",
                        command="echo Hello World",
                        timeout_second=1,
                    ),
                ]
            ),
            artifact=ArtifactConfig(output_dir="./artifact/success_runner_conifg"),
        ),
    ],
)
def test_runner_executes_all_steps_when_success(config):
    executor = MockSuccessExecutor()
    runner = DeviceTestRunner(executor=executor, reporter=JsonReporter())
    result = runner.run(config)

    assert result.test_case_name == "success_runner"
    assert result.passed is True
    assert len(result.step_results) == 2
    assert executor.executed_steps == ["1st step", "2nd step"]


class MockFailedExecutor:
    def __init__(self):
        self.executed_steps = []

    def execute(self, step: WorkflowStep) -> StepResult:
        self.executed_steps.append(step.name)

        if step.name == "2nd step":
            return StepResult(
                name=step.name,
                command=step.command,
                success=False,
                exit_code=1,
                duration_seconds=2,
                stdout="",
                stderr="failed",
            )

        return StepResult(
            name=step.name,
            command=step.command,
            success=True,
            exit_code=0,
            duration_seconds=2,
            stdout="ok",
            stderr="",
        )


@pytest.mark.parametrize(
    argnames="config",
    argvalues=[
        RunnerConfig(
            test_case=DeviceTestCase(id="002", name="failed_runner", description="failed"),
            device=DeviceInfo(serial="0000000000", product="faker_product", build="123456"),
            workflow=Workflow(
                steps=[
                    WorkflowStep(
                        name="1st step",
                        type="command",
                        command="echo Hello World",
                        timeout_second=1,
                    ),
                    WorkflowStep(
                        name="2nd step",
                        type="command",
                        command="exit 1",
                        timeout_second=1,
                    ),
                    WorkflowStep(
                        name="3rd step",
                        type="command",
                        command="echo Hello World",
                        timeout_second=1,
                    ),
                ]
            ),
            artifact=ArtifactConfig(output_dir="./artifact/failed_runner_conifg"),
        ),
    ],
)
def test_runner_terminate_when_step_failed(config):
    executor = MockFailedExecutor()
    runner = DeviceTestRunner(executor=executor, reporter=JsonReporter())
    result = runner.run(config)

    assert result.test_case_name == "failed_runner"
    assert result.passed is False
    assert len(result.step_results) == 2
    assert executor.executed_steps == ["1st step", "2nd step"]

    assert result.step_results[0].exit_code == 0
    assert result.step_results[1].exit_code == 1
