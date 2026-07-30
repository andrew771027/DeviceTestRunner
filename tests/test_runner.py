from pathlib import Path
from typing import List

import pytest

from runner.models import (
    ArtifactConfig,
    DeviceInfo,
    DeviceTestCase,
    LifecycleConfig,
    LifecycleStepContent,
    LifecycleSteps,
    RunnerConfig,
    StepResult,
)
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner
from runner.artifact import StepLogWriter

class MockExecutor:

    def __init__(self, failed_step_name: str | None = None):
        self.failed_step_name = failed_step_name
        self.executed_steps: List[tuple[str, str]] = []

    def execute(self, step: LifecycleStepContent, stage: str, log_writer: StepLogWriter) -> StepResult:
        self.executed_steps.append(step.name)

        success = step.name != self.failed_step_name

        log_writer.write_stdout(f"{step.name} stdout\n")

        if not success:
            log_writer.write_stderr(f"{step.name} failed\n")

        return StepResult(
            stage=stage,
            name=step.name,
            command=step.command,
            success=success,
            exit_code=0 if success else 1,
            duration_seconds=0.01,
            stdout=log_writer.stdout_path,
            stderr=log_writer.stderr_path,
            stdout_log_path=str(log_writer.stdout_path),
            stderr_log_path=str(log_writer.stderr_path),
        )


def mock_step(name: str) -> LifecycleStepContent:
    return LifecycleStepContent(
        name=name,
        type="command",
        command=f"echo {name}",
        timeout_second=10,
    )


def mock_config(
    tmp_path: Path,
) -> RunnerConfig:
    return RunnerConfig(
        test_case=DeviceTestCase(
            id="power_001",
            name="power_001",
            description="Description",
        ),
        device=DeviceInfo(
            serial="device_001",
            product="pixel",
            build="build_001",
        ),
        lifecycle=LifecycleConfig(
            global_setup=LifecycleSteps(steps=[mock_step("global_setup")]),
            setup=LifecycleSteps(steps=[mock_step("setup")]),
            scenario=LifecycleSteps(
                steps=[
                    mock_step("scenario_1"),
                    mock_step("scenario_2"),
                ]
            ),
            teardown=LifecycleSteps(steps=[mock_step("teardown")]),
            global_teardown=LifecycleSteps(steps=[mock_step("global_teardown")]),
        ),
        artifact=ArtifactConfig(
            output_dir=str(tmp_path),
        ),
    )


def test_runner_executes_all_stages_and_all_steps_success(tmp_path):
    config = mock_config(tmp_path)
    executor = MockExecutor()
    runner = DeviceTestRunner(executor=executor, reporter=JsonReporter())
    result = runner.run(config)

    assert result.metadata.test_case_name == "power_001"
    assert result.passed is True

    assert result.summary.status == "PASSED"

    assert len(result.step_results) == 6

    assert result.summary.configured_steps == 6
    assert result.summary.executed_steps == 6
    assert result.summary.passed_steps == 6
    assert result.summary.failed_steps == 0
    assert result.summary.skipped_steps == 0

    assert executor.executed_steps == [
        "global_setup",
        "setup",
        "scenario_1",
        "scenario_2",
        "teardown",
        "global_teardown",
    ]

    first_result = result.step_results[0]
    stdout_path = Path(first_result.stdout_log_path)
    stderr_path = Path(first_result.stderr_log_path)
    assert stdout_path.read_text(encoding="utf-8") == "global_setup stdout\n"
    assert stderr_path.read_text(encoding="utf-8") == ""
    
    assert result.step_results[0].stderr == ""
    assert result.step_results[1].stderr == ""
    assert result.step_results[2].stderr == ""
    assert result.step_results[3].stderr == ""
    assert result.step_results[4].stderr == ""
    assert result.step_results[5].stderr == ""


@pytest.mark.parametrize(
    argnames="failed_step_name",
    argvalues=["scenario_2"],
)
def test_runner_terminate_when_step_failed(tmp_path, failed_step_name):
    config = mock_config(tmp_path)
    executor = MockExecutor(failed_step_name=failed_step_name)
    runner = DeviceTestRunner(executor=executor, reporter=JsonReporter())
    result = runner.run(config)

    assert result.metadata.test_case_name == "power_001"
    assert result.passed is False

    assert len(result.step_results) == 6

    assert result.summary.configured_steps == 6
    assert result.summary.executed_steps == 6
    assert result.summary.passed_steps == 5
    assert result.summary.failed_steps == 1
    assert result.summary.skipped_steps == 0

    assert executor.executed_steps == [
        "global_setup",
        "setup",
        "scenario_1",
        "scenario_2",
        "teardown",
        "global_teardown",
    ]

    assert [step.name for step in result.step_results if step.passed is True] == [
        "global_setup",
        "setup",
        "scenario_1",
        "teardown",
        "global_teardown",
    ]

    assert [step.name for step in result.step_results if step.passed is False] == [failed_step_name]

    assert result.summary.status == "FAILED"

    assert result.step_results[0].exit_code == 0
    assert result.step_results[1].exit_code == 0
    assert result.step_results[2].exit_code == 0
    assert result.step_results[3].exit_code == 1
    assert result.step_results[4].exit_code == 0
    assert result.step_results[5].exit_code == 0

    assert result.step_results[0].stderr == ""
    assert result.step_results[1].stderr == ""
    assert result.step_results[2].stderr == ""
    assert result.step_results[3].stderr == f"{failed_step_name} failed"
    assert result.step_results[4].stderr == ""
    assert result.step_results[5].stderr == ""

    failed_step_result = next(step for step in result.step_results if step.name == failed_step_name)
    assert failed_step_result.stage == "scenario"
    assert failed_step_result.name == "scenario_2"
    assert Path(failed_step_result.stdout_log_path).exists()
    assert Path(failed_step_result.stderr_log_path).exists()
    assert "scenario_2 failed" in Path(failed_step_result.stderr_log_path).read_text(encoding="utf-8")




@pytest.mark.parametrize(argnames="failed_step_name", argvalues=["global_setup"])
def test_global_setup_failure_only_run_global_teardown(tmp_path, failed_step_name):
    config = mock_config(tmp_path)
    executor = MockExecutor(failed_step_name=failed_step_name)
    runner = DeviceTestRunner(executor=executor, reporter=JsonReporter())
    result = runner.run(config)

    assert result.metadata.test_case_name == "power_001"
    assert result.passed is False

    assert len(result.step_results) == 1

    assert result.summary.configured_steps == 6
    assert result.summary.executed_steps == 1
    assert result.summary.passed_steps == 0
    assert result.summary.failed_steps == 1
    assert result.summary.skipped_steps == 5

    assert executor.executed_steps == [
        "global_setup",
    ]

    assert [step.name for step in result.step_results if step.passed is True] == []

    assert [step.name for step in result.step_results if step.passed is False] == [
        failed_step_name,
    ]

    assert result.summary.status == "FAILED"

    assert result.step_results[0].exit_code == 1

    assert result.step_results[0].stderr == f"{failed_step_name} failed"


@pytest.mark.parametrize(argnames="failed_step_name", argvalues=["setup"])
def test_setup_failure_only_run_teardown_and_global_teardown(tmp_path, failed_step_name):
    config = mock_config(tmp_path)
    executor = MockExecutor(failed_step_name=failed_step_name)
    runner = DeviceTestRunner(executor=executor, reporter=JsonReporter())
    result = runner.run(config)

    assert result.metadata.test_case_name == "power_001"
    assert result.passed is False

    assert len(result.step_results) == 3

    assert result.summary.configured_steps == 6
    assert result.summary.executed_steps == 3
    assert result.summary.passed_steps == 2
    assert result.summary.failed_steps == 1
    assert result.summary.skipped_steps == 3

    assert [step.name for step in result.step_results if step.passed is True] == [
        "global_setup",
        "global_teardown",
    ]

    assert [step.name for step in result.step_results if step.passed is False] == [
        failed_step_name,
    ]

    assert result.summary.status == "FAILED"

    assert result.step_results[0].exit_code == 0
    assert result.step_results[1].exit_code == 1
    assert result.step_results[2].exit_code == 0

    assert result.step_results[0].stderr == ""
    assert result.step_results[1].stderr == f"{failed_step_name} failed"
    assert result.step_results[2].stderr == ""
