from pathlib import Path
from typing import List

import pytest

from runner.artifact import ArtifactManager, StepLogWriter
from runner.artifact_validator import ArtifactValidator
from runner.models import (
    ArtifactConfig,
    ArtifactValidationConfig,
    ArtifactValidationRule,
    DeviceInfo,
    DeviceTestCase,
    LifecycleConfig,
    LifecycleStepContent,
    LifecycleSteps,
    RetryConfig,
    RunnerConfig,
    StepAttemptResult,
)
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner


def result_passed(result) -> bool:
    return all(
        (step.attempt_results and step.attempt_results[-1].exit_code == 0)
        for step in result.step_results
    )


class MockExecutor:

    def __init__(self, failed_step_name: str | None = None):
        self.failed_step_name = failed_step_name
        self.executed_attempts: List[tuple[str, int]] = []

    def execute(
        self,
        step: LifecycleStepContent,
        stage: str,
        attempt: int,
        log_writer: StepLogWriter,
        working_directory: str | Path,
    ) -> StepAttemptResult:

        working_directory = Path(working_directory)

        output_path = working_directory / "results" / "test_file.txt"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text("Hello World", encoding="utf-8")

        self.executed_attempts.append((step.name, attempt))

        success = step.name != self.failed_step_name

        stdout = f"{step.name} stdout"
        stderr = ""

        log_writer.write_stdout(stdout)

        if not success:
            stderr = f"{step.name} failed"
            log_writer.write_stderr(stderr)

        return StepAttemptResult(
            attempt=attempt,
            success=success,
            exit_code=0 if success else 1,
            duration_seconds=0.01,
            stdout=stdout,
            stderr=stderr,
            stdout_log_path=str(log_writer.stdout_path),
            stderr_log_path=str(log_writer.stderr_path),
            error=None,
        )


class MockFailedOnceExecutor:

    def __init__(self):
        self.failed_once = False

    def execute(
        self,
        step: LifecycleStepContent,
        stage: str,
        attempt: int,
        log_writer: StepLogWriter,
        working_directory: str | Path,
    ) -> StepAttemptResult:

        if not self.failed_once:
            self.failed_once = True
            success = False
            log_writer.write_stderr("temporary failure\n")
        else:
            success = True
            log_writer.write_stdout("success\n")

        return StepAttemptResult(
            attempt=attempt,
            success=success,
            exit_code=(0 if success else 1),
            duration_seconds=0.01,
            stdout=log_writer.stdout,
            stderr=log_writer.stderr,
            stdout_log_path=str(log_writer.stdout_path),
            stderr_log_path=str(log_writer.stderr_path),
        )


class MockAlwaysFailExecutor:
    def __init__(self):
        self.call_count = 0

    def execute(
        self,
        step: LifecycleStepContent,
        stage: str,
        attempt: int,
        log_writer: StepLogWriter,
        working_directory: str | Path,
    ) -> StepAttemptResult:

        self.call_count += 1

        log_writer.write_stderr("failed\n")

        return StepAttemptResult(
            attempt=attempt,
            success=False,
            exit_code=1,
            duration_seconds=0.01,
            stdout=log_writer.stdout,
            stderr=log_writer.stderr,
            stdout_log_path=str(log_writer.stdout_path),
            stderr_log_path=str(log_writer.stderr_path),
        )


class MockAlwaysPassExecutor:
    def __init__(self):
        self.call_count = 0

    def execute(
        self,
        step: LifecycleStepContent,
        stage: str,
        attempt: int,
        log_writer: StepLogWriter,
        working_directory: str | Path,
    ) -> StepAttemptResult:

        self.call_count += 1

        log_writer.write_stderr("success\n")

        return StepAttemptResult(
            attempt=attempt,
            success=True,
            exit_code=0,
            duration_seconds=0.01,
            stdout=log_writer.stdout,
            stderr=log_writer.stderr,
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


def mock_config(tmp_path: Path, min_size_bytes: int = 1) -> RunnerConfig:
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
        retry=RetryConfig(
            max_attempts=3,
            delay_seconds=1,
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
            validation=ArtifactValidationConfig(
                rules=[
                    ArtifactValidationRule(
                        name="test_file_exist",
                        type="exists",
                        path="results/test_file.txt",
                    ),
                    ArtifactValidationRule(
                        name="test_file_size",
                        type="file_size",
                        path="results/test_file.txt",
                        min_size_bytes=min_size_bytes,
                    ),
                ]
            ),
        ),
    )


def mock_retry_config(tmp_path: Path) -> RunnerConfig:
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
        retry=RetryConfig(
            max_attempts=2,
            delay_seconds=2,
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


@pytest.mark.test_lifecycle
def test_runner_executes_all_stages_and_all_steps_success(tmp_path: Path):
    config = mock_config(tmp_path)
    executor = MockExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    assert result.metadata.test_case_name == "power_001"
    assert result_passed(result) is True

    assert result.summary.status == "PASSED"

    assert len(result.step_results) == 6

    assert result.summary.configured_steps == 6
    assert result.summary.executed_steps == 6
    assert result.summary.passed_steps == 6
    assert result.summary.failed_steps == 0
    assert result.summary.skipped_steps == 0

    assert executor.executed_attempts == [
        ("global_setup", 1),
        ("setup", 1),
        ("scenario_1", 1),
        ("scenario_2", 1),
        ("teardown", 1),
        ("global_teardown", 1),
    ]

    first_result = result.step_results[0]
    stdout_path = Path(first_result.attempt_results[-1].stdout_log_path)
    stderr_path = Path(first_result.attempt_results[-1].stderr_log_path)
    assert stdout_path.read_text(encoding="utf-8") == "global_setup stdout"
    assert stderr_path.read_text(encoding="utf-8") == ""

    assert result.step_results[0].attempt_results[-1].stderr == ""
    assert result.step_results[1].attempt_results[-1].stderr == ""
    assert result.step_results[2].attempt_results[-1].stderr == ""
    assert result.step_results[3].attempt_results[-1].stderr == ""
    assert result.step_results[4].attempt_results[-1].stderr == ""
    assert result.step_results[5].attempt_results[-1].stderr == ""


@pytest.mark.test_lifecycle
@pytest.mark.parametrize(
    argnames="failed_step_name",
    argvalues=["scenario_2"],
)
def test_runner_terminate_when_step_failed(tmp_path, failed_step_name):
    config = mock_config(tmp_path)
    executor = MockExecutor(failed_step_name=failed_step_name)
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    assert result.metadata.test_case_name == "power_001"
    assert result_passed(result) is False

    assert len(result.step_results) == 6

    assert result.summary.configured_steps == 6
    assert result.summary.executed_steps == 6
    assert result.summary.passed_steps == 5
    assert result.summary.failed_steps == 1
    assert result.summary.skipped_steps == 0

    assert [step.name for step in result.step_results] == [
        "global_setup",
        "setup",
        "scenario_1",
        "scenario_2",
        "teardown",
        "global_teardown",
    ]

    assert executor.executed_attempts == [
        ("global_setup", 1),
        ("setup", 1),
        ("scenario_1", 1),
        ("scenario_2", 1),
        ("scenario_2", 2),
        ("scenario_2", 3),
        ("teardown", 1),
        ("global_teardown", 1),
    ]

    assert [step.name for step in result.step_results if step.success is True] == [
        "global_setup",
        "setup",
        "scenario_1",
        "teardown",
        "global_teardown",
    ]

    assert [step.name for step in result.step_results if step.success is False] == [
        failed_step_name
    ]

    assert result.summary.status == "FAILED"

    assert result.step_results[0].attempt_results[-1].exit_code == 0
    assert result.step_results[1].attempt_results[-1].exit_code == 0
    assert result.step_results[2].attempt_results[-1].exit_code == 0
    assert result.step_results[3].attempt_results[-1].exit_code == 1
    assert result.step_results[4].attempt_results[-1].exit_code == 0
    assert result.step_results[5].attempt_results[-1].exit_code == 0

    assert result.step_results[0].attempt_results[-1].stderr == ""
    assert result.step_results[1].attempt_results[-1].stderr == ""
    assert result.step_results[2].attempt_results[-1].stderr == ""
    assert (
        result.step_results[3].attempt_results[-1].stderr
        == f"{failed_step_name} failed"
    )
    assert result.step_results[4].attempt_results[-1].stderr == ""
    assert result.step_results[5].attempt_results[-1].stderr == ""

    failed_step_result = next(
        step for step in result.step_results if step.name == failed_step_name
    )
    assert failed_step_result.stage == "scenario"
    assert failed_step_result.name == failed_step_name
    assert Path(failed_step_result.attempt_results[-1].stdout_log_path).exists()
    assert Path(failed_step_result.attempt_results[-1].stderr_log_path).exists()
    assert f"{failed_step_name} failed" in Path(
        failed_step_result.attempt_results[-1].stderr_log_path
    ).read_text(encoding="utf-8")


@pytest.mark.test_lifecycle
@pytest.mark.parametrize(argnames="failed_step_name", argvalues=["global_setup"])
def test_global_setup_failure_only_run_global_teardown(tmp_path, failed_step_name):
    config = mock_config(tmp_path)
    executor = MockExecutor(failed_step_name=failed_step_name)
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    assert result.metadata.test_case_name == "power_001"
    assert result_passed(result) is False

    assert len(result.step_results) == 1

    assert result.summary.configured_steps == 6
    assert result.summary.executed_steps == 1
    assert result.summary.passed_steps == 0
    assert result.summary.failed_steps == 1
    assert result.summary.skipped_steps == 5

    assert executor.executed_attempts == [
        ("global_setup", 1),
        ("global_setup", 2),
        ("global_setup", 3),
    ]

    assert [step.name for step in result.step_results if step.success is True] == []

    assert [step.name for step in result.step_results if step.success is False] == [
        failed_step_name,
    ]

    assert result.summary.status == "FAILED"

    assert result.step_results[0].attempt_results[-1].exit_code == 1

    assert (
        result.step_results[0].attempt_results[-1].stderr
        == f"{failed_step_name} failed"
    )


@pytest.mark.test_lifecycle
@pytest.mark.parametrize(argnames="failed_step_name", argvalues=["setup"])
def test_setup_failure_only_run_global_teardown(tmp_path, failed_step_name):
    config = mock_config(tmp_path)
    executor = MockExecutor(failed_step_name=failed_step_name)
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    assert result.metadata.test_case_name == "power_001"
    assert result_passed(result) is False

    assert len(result.step_results) == 3

    assert result.summary.configured_steps == 6
    assert result.summary.executed_steps == 3
    assert result.summary.passed_steps == 2
    assert result.summary.failed_steps == 1
    assert result.summary.skipped_steps == 3

    assert [step.name for step in result.step_results if step.success is True] == [
        "global_setup",
        "global_teardown",
    ]

    assert [step.name for step in result.step_results if step.success is False] == [
        failed_step_name,
    ]

    assert result.summary.status == "FAILED"

    assert result.step_results[0].attempt_results[-1].exit_code == 0
    assert result.step_results[1].attempt_results[-1].exit_code == 1
    assert result.step_results[2].attempt_results[-1].exit_code == 0

    assert result.step_results[0].attempt_results[-1].stderr == ""
    assert (
        result.step_results[1].attempt_results[-1].stderr
        == f"{failed_step_name} failed"
    )
    assert result.step_results[2].attempt_results[-1].stderr == ""

    failed_step_result = next(
        step for step in result.step_results if step.name == failed_step_name
    )
    assert failed_step_result.stage == "setup"
    assert failed_step_result.name == failed_step_name
    assert Path(failed_step_result.attempt_results[-1].stdout_log_path).exists()
    assert Path(failed_step_result.attempt_results[-1].stderr_log_path).exists()
    assert f"{failed_step_name} failed" in Path(
        failed_step_result.attempt_results[-1].stderr_log_path
    ).read_text(encoding="utf-8")

    executed_names = [name for name, _ in runner.executor.executed_attempts]
    assert "global_setup" in (executed_names)
    assert "setup" in (executed_names)
    assert "global_teardown" in (executed_names)


@pytest.mark.artifact
def test_runner_passes_when_artifacts_are_valid(tmp_path: Path):
    config = mock_config(tmp_path)
    executor = MockExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    assert result.summary.status == "PASSED"
    assert result.summary.configured_artifact_rules == 2
    assert result.summary.passed_artifact_rules == 2
    assert result.summary.failed_artifact_rules == 0
    assert all(validation.passed for validation in result.artifact_validation_results)


@pytest.mark.artifact
def test_runner_fails_when_artifacts_invalid(tmp_path: Path):
    config = mock_config(tmp_path, min_size_bytes=10_000)
    executor = MockExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    assert result.summary.passed_steps == 6
    assert result.summary.failed_steps == 0

    assert result.summary.status == "FAILED"

    assert result.summary.failed_artifact_rules == 1

    failed_validation = next(
        validation
        for validation in result.artifact_validation_results
        if not validation.passed
    )

    assert failed_validation.name == "test_file_size"
    assert "smaller than the minimum" in (failed_validation.message)


@pytest.mark.artifact
def test_runner_passes_without_validation_rules(tmp_path: Path):

    config = RunnerConfig(
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
        retry=RetryConfig(
            max_attempts=3,
            delay_seconds=1,
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

    executor = MockExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    assert result.summary.status == "PASSED"
    assert result.summary.configured_steps == 6
    assert result.summary.passed_steps == 6
    assert result.summary.executed_steps == 6
    assert result.summary.skipped_steps == 0
    assert result.summary.failed_steps == 0

    assert result.summary.configured_artifact_rules == 0
    assert result.artifact_validation_results == []


@pytest.mark.retry
def test_step_passes_after_retry(tmp_path: Path):
    config = mock_retry_config(tmp_path)
    executor = MockFailedOnceExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    assert result.summary.status == "PASSED"

    step_result = result.step_results[0]

    assert step_result.attempts == 2
    assert len(step_result.attempt_results) == 2
    assert step_result.attempt_results[0].success is False
    assert step_result.attempt_results[1].success is True


@pytest.mark.retry
def test_step_fails_after_max_attempts(tmp_path: Path):
    config = mock_retry_config(tmp_path)
    executor = MockAlwaysFailExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    assert result.summary.status == "FAILED"

    step_result = result.step_results[0]

    assert step_result.attempts == 2
    assert len(step_result.attempt_results) == 2
    assert step_result.attempt_results[0].success is False
    assert step_result.attempt_results[1].success is False


@pytest.mark.retry
def test_successful_step_is_not_retried(tmp_path: Path):

    config = mock_retry_config(tmp_path)
    executor = MockAlwaysPassExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    assert result.step_results[0].attempts == 1
    assert result.summary.status == "PASSED"


@pytest.mark.retry
def test_retry_creates_separate_log_files(tmp_path: Path):

    config = mock_retry_config(tmp_path)
    executor = MockFailedOnceExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    step_result = result.step_results[0]
    attempt_1 = step_result.attempt_results[0]

    assert Path(attempt_1.stderr_log_path).exists()
    assert "attempt_1" in attempt_1.stderr_log_path

    attempt_2 = step_result.attempt_results[1]

    assert Path(attempt_2.stdout_log_path).exists()
    assert "attempt_2" in attempt_2.stdout_log_path


@pytest.mark.retry
def test_retry_waits_between_attempts(tmp_path, monkeypatch):

    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr("runner.runner.time.sleep", fake_sleep)

    config = mock_retry_config(tmp_path)
    executor = MockFailedOnceExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
    )

    runner.run(config)

    assert sleep_calls == [2]
