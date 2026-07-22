import pytest

from runner.models import (
    ArtifactConfig,
    DeviceInfo,
    DeviceTestCase,
    RunnerConfig,
    StepResult,
    LifecycleConfig,
    LifecycleSteps,
    LifecycleStepContent,
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
        lifecycle=LifecycleConfig(
            global_setup=LifecycleSteps(
                steps=[LifecycleStepContent(
                    name="global_setup",
                    type="command",
                    command="echo 'global_setup'",
                    timeout_second=10,
                ),
                ],
            ),
            setup=LifecycleSteps(
                steps=[LifecycleStepContent(
                    name="setup",
                    type="command",
                    command="echo 'setup'",
                    timeout_second=10,
                ),
                ],
            ),
            scenario=LifecycleSteps(
                steps=[LifecycleStepContent(
                    name="scenario 1",
                    type="command",
                    command="echo 'scenario'",
                    timeout_second=30,
                ),
                    LifecycleStepContent(
                        name="scenario 2",
                        type="command",
                        command="echo 'scenario'",
                        timeout_second=30,
                ),
                ],
            ),
            teardown=LifecycleSteps(
                steps=[LifecycleStepContent(
                    name="teardown",
                    type="command",
                    command="echo 'teardown'",
                    timeout_second=10,
                ),
                ],
            ),
            global_teardown=LifecycleSteps(
                steps=[LifecycleStepContent(
                    name="global_teardown",
                    type="command",
                    command="echo 'global_teardown'",
                    timeout_second=10,
                ),
                ],
            ),
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
        lifecycle=LifecycleConfig(
            global_setup=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="global_setup",
                        type="command",
                        command="echo 'global_setup'",
                        timeout_second=10,
                    )
                ]
            ),
            
            setup=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="setup",
                        type="command",
                        command="echo 'setup'",
                        timeout_second=10,
                    )
                ]
            ),
            scenario=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                    name="scenario success",
                    type="command",
                    command="echo 'scenario'",
                    timeout_second=30,
                    ),
                    LifecycleStepContent(
                    name="scenario failed",
                    type="command",
                    command="exit 1",
                    timeout_second=30,
                    ),
                ]
            ),
            teardown=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="teardown",
                        type="command",
                        command="echo 'teardown'",
                        timeout_second=10,
                    )
                ]
            ),
            global_teardown=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="global_teardown",
                        type="command",
                        command="echo 'global_teardown'",
                        timeout_second=10,
                    )
                ]
            ),
        ),
        artifact=ArtifactConfig(
            output_dir="artifact/sample_device_config",
        ),
    )


class MockSuccessExecutor:
    def __init__(self):
        self.executed_steps = []

    def execute(self, step: LifecycleStepContent, stage: str) -> StepResult:
        self.executed_steps.append(step.name)

        return StepResult(
            stage=stage,
            name=step.name,
            command=step.command,
            success=True,
            exit_code=0,
            duration_seconds=0,
            stdout="ok",
            stderr="",
        )


class MockFailedExecutor:
    def __init__(self):
        self.executed_steps = []

    def execute(self, step: LifecycleStepContent, stage: str) -> StepResult:
        self.executed_steps.append(step.name)

        if step.name == "scenario failed":
            return StepResult(
                stage=stage,
                name=step.name,
                command=step.command,
                success=False,
                exit_code=1,
                duration_seconds=2,
                stdout="",
                stderr="failed",
            )

        return StepResult(
            stage=stage,
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
    argvalues=[build_success_runner_config()],
)
def test_runner_executes_all_steps_when_success(config):
    executor = MockSuccessExecutor()
    runner = DeviceTestRunner(executor=executor, reporter=JsonReporter())
    result = runner.run(config)

    assert result.metadata.test_case_name == "Youtube Playback Power Test (Success)"
    assert result.passed is True
    assert len(result.step_results) == 6
    assert executor.executed_steps == ["global_setup", "setup", "scenario 1", "scenario 2", "teardown", "global_teardown"]


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
    
    assert result.summary.configured_steps == 6
    assert result.summary.executed_steps == 6
    assert result.summary.passed_steps == 5
    assert result.summary.failed_steps == 1
    assert result.summary.skipped_steps == 0

    assert sorted(executor.executed_steps) == sorted(["global_setup", "setup", "scenario success", "scenario failed", "teardown", "global_teardown"])
    assert sorted([step.name for step in result.step_results if step.passed is True]) == sorted(["global_setup", "setup", "scenario success", "teardown", "global_teardown"])
    assert sorted([step.name for step in result.step_results if step.passed is False]) == sorted(["scenario failed"])

    assert result.step_results[0].exit_code == 0
    assert result.step_results[1].exit_code == 0
    assert result.step_results[2].exit_code == 0
    assert result.step_results[3].exit_code == 1
    assert result.step_results[4].exit_code == 0
    assert result.step_results[5].exit_code == 0