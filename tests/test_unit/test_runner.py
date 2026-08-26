from pathlib import Path
from typing import List

import pytest

from runner.artifact import ArtifactManager, StepLogWriter
from runner.artifact_validator import ArtifactValidator
from runner.failure import FailureClassifier
from runner.models import (
    ArtifactConfig,
    ArtifactValidationConfig,
    ArtifactValidationResult,
    ArtifactValidationRule,
    DeviceInfo,
    DeviceTestCase,
    FailureType,
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
            failure_type=FailureType.NONE if success else FailureType.PROCESS_ERROR,
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
            failure_type=FailureType.NONE if success else FailureType.PROCESS_ERROR,
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
            failure_type=FailureType.PROCESS_ERROR,
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

        log_writer.write_stderr(f"attempt {attempt}\n")

        return StepAttemptResult(
            attempt=attempt,
            success=True,
            failure_type=FailureType.NONE,
            exit_code=0,
            duration_seconds=0.01,
            stdout=log_writer.stdout,
            stderr=log_writer.stderr,
            stdout_log_path=str(log_writer.stdout_path),
            stderr_log_path=str(log_writer.stderr_path),
        )


class MockFailedOnceArtifactValidator:
    def __init__(self):
        self.failed_once = False

    def validate_all(
        self, rules: List[ArtifactValidationRule], base_dir: str | Path
    ) -> List[ArtifactValidationResult]:
        if not self.failed_once:
            self.failed_once = True
            passed = False
        else:
            passed = True

        return [
            ArtifactValidationResult(
                name="mock_csv",
                type="csv_content",
                path="mock_csv.csv",
                passed=passed,
                failure_type=(FailureType.NONE if passed else FailureType.ARTIFACT_INVALID),
                message=("valid" if passed else "invalid"),
            )
        ]


class MockAlwaysFailArtifactValidator:
    def validate_all(self, rules: List[ArtifactValidationRule], base_dir: str | Path):
        return [
            ArtifactValidationResult(
                name="mock_test",
                type="csv_content",
                path="mock.csv",
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message="invalid artifact",
            )
        ]


class MockMissingThenPassValidator:
    def __init__(self):
        self.failed_once = False

    def validate_all(self, rules, base_dir):

        if not self.failed_once:
            self.failed_once = True
            passed = False
        else:
            passed = True

        if passed is False:
            return [
                ArtifactValidationResult(
                    name="power",
                    type="exists",
                    path="power.csv",
                    passed=False,
                    failure_type=(FailureType.ARTIFACT_MISSING),
                    message="missing",
                )
            ]

        return [
            ArtifactValidationResult(
                name="power",
                type="exists",
                path="power.csv",
                passed=True,
                failure_type=(FailureType.NONE),
                message="valid",
            )
        ]


def mock_step(name: str) -> LifecycleStepContent:
    return LifecycleStepContent(
        name=name,
        type="command",
        command=f"echo {name}",
        timeout_second=10,
    )


def mock_artifact_step(name: str, path: str | Path):
    path = Path(path)
    if not path.exists():
        path.write_text("Hello World", encoding="utf-8")

    return LifecycleStepContent(
        name=name,
        type="command",
        command="echo Hello World",
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
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then runner executes all stages and all steps success.
    """
    config = mock_config(tmp_path)
    executor = MockExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
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
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then runner terminate when step failed.
    """
    config = mock_config(tmp_path)
    executor = MockExecutor(failed_step_name=failed_step_name)
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
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
    assert result.step_results[3].attempt_results[-1].stderr == f"{failed_step_name} failed"
    assert result.step_results[4].attempt_results[-1].stderr == ""
    assert result.step_results[5].attempt_results[-1].stderr == ""

    failed_step_result = next(step for step in result.step_results if step.name == failed_step_name)
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
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then global setup failure only run global teardown.
    """
    config = mock_config(tmp_path)
    executor = MockExecutor(failed_step_name=failed_step_name)
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    assert result.metadata.test_case_name == "power_001"
    assert result_passed(result) is False

    assert len(result.step_results) == 2

    assert result.summary.configured_steps == 6
    assert result.summary.executed_steps == 2
    assert result.summary.passed_steps == 1
    assert result.summary.failed_steps == 1
    assert result.summary.skipped_steps == 4

    assert executor.executed_attempts == [
        ("global_setup", 1),
        ("global_setup", 2),
        ("global_setup", 3),
        ("global_teardown", 1),
    ]

    assert [step.name for step in result.step_results if step.success is True] == [
        "global_teardown"
    ]

    assert [step.name for step in result.step_results if step.success is False] == [
        failed_step_name,
    ]

    assert result.summary.status == "FAILED"

    # global setup
    assert result.step_results[0].attempt_results[-1].exit_code == 1
    # global teardown
    assert result.step_results[1].attempt_results[-1].exit_code == 0

    assert result.step_results[0].attempt_results[-1].stderr == f"{failed_step_name} failed"
    assert result.step_results[1].attempt_results[-1].stderr == ""


@pytest.mark.test_lifecycle
@pytest.mark.parametrize(argnames="failed_step_name", argvalues=["setup"])
def test_setup_failure_skips_scenario_but_runs_teardown_and_global_teardown(
    tmp_path, failed_step_name
):
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then setup failure skips scenario but runs teardown and global teardown.
    """
    config = mock_config(tmp_path)
    executor = MockExecutor(failed_step_name=failed_step_name)
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    assert result.metadata.test_case_name == "power_001"
    assert result_passed(result) is False

    assert len(result.step_results) == 4

    assert result.summary.configured_steps == 6
    assert result.summary.executed_steps == 4
    assert result.summary.passed_steps == 3
    assert result.summary.failed_steps == 1
    assert result.summary.skipped_steps == 2

    assert [step.name for step in result.step_results if step.success is True] == [
        "global_setup",
        "teardown",
        "global_teardown",
    ]

    assert [step.name for step in result.step_results if step.success is False] == [
        failed_step_name,
    ]

    assert result.summary.status == "FAILED"

    # global setup
    assert result.step_results[0].attempt_results[-1].exit_code == 0
    # setup
    assert result.step_results[1].attempt_results[-1].exit_code == 1
    # teardown
    assert result.step_results[2].attempt_results[-1].exit_code == 0
    # global_teardown
    assert result.step_results[3].attempt_results[-1].exit_code == 0

    assert result.step_results[0].attempt_results[-1].stderr == ""
    assert result.step_results[1].attempt_results[-1].stderr == f"{failed_step_name} failed"
    assert result.step_results[2].attempt_results[-1].stderr == ""
    assert result.step_results[3].attempt_results[-1].stderr == ""

    failed_step_result = next(step for step in result.step_results if step.name == failed_step_name)
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
    assert "teardown" in (executed_names)
    assert "global_teardown" in (executed_names)


@pytest.mark.artifact
def test_runner_passes_when_artifacts_are_valid(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then runner is accepted when artifacts are valid.
    """
    config = mock_config(tmp_path)
    executor = MockExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
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
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then runner is rejected when artifacts invalid, with a diagnostic failure result.
    """
    config = mock_config(tmp_path, min_size_bytes=10_000)
    executor = MockExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    assert result.summary.passed_steps == 6
    assert result.summary.failed_steps == 0

    assert result.summary.status == "FAILED"

    assert result.summary.failed_artifact_rules == 1

    failed_validation = next(
        validation for validation in result.artifact_validation_results if not validation.passed
    )

    assert failed_validation.name == "test_file_size"
    assert "smaller than the minimum" in (failed_validation.message)


@pytest.mark.artifact
def test_runner_passes_without_validation_rules(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then runner passes without validation rules.
    """

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
        failure_classifier=FailureClassifier(),
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
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then step passes after retry.
    """
    config = mock_retry_config(tmp_path)
    executor = MockFailedOnceExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
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
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then step fails after max attempts.
    """
    config = mock_retry_config(tmp_path)
    executor = MockAlwaysFailExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
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
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then successful step is not retried.
    """

    config = mock_retry_config(tmp_path)
    executor = MockAlwaysPassExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    assert result.step_results[0].attempts == 1
    assert result.summary.status == "PASSED"


@pytest.mark.retry
def test_retry_creates_separate_log_files(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then retry creates separate log files.
    """

    config = mock_retry_config(tmp_path)
    executor = MockFailedOnceExecutor()
    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
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
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then retry waits between attempts.
    """

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
        failure_classifier=FailureClassifier(),
        reporter=JsonReporter(),
    )

    runner.run(config)

    assert sleep_calls == [2]


@pytest.mark.artifact
@pytest.mark.retry
def test_artifact_failure_triggers_retry(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then artifact failure triggers retry.
    """

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
                    mock_artifact_step("scenario_1", tmp_path / "test_file.txt"),
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
                        path=tmp_path / "test_file.txt",
                        after_step="scenario_1",
                        retry_on_failure=True,
                    ),
                ]
            ),
        ),
    )

    executor = MockAlwaysPassExecutor()
    validator = MockFailedOnceArtifactValidator()

    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=ArtifactManager(output_dir=tmp_path),
        artifact_validator=validator,
        failure_classifier=FailureClassifier(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    # global_setup
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "global_setup"
    ][0]
    assert step_result.success is True
    assert step_result.attempts == 1
    assert step_result.attempt_results[0].success is True

    # setup
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "setup"
    ][0]
    assert step_result.success is True
    assert step_result.attempts == 1
    assert step_result.attempt_results[0].success is True

    # scenario.scenario_1
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "scenario_1"
    ][0]
    assert step_result.success is True
    assert step_result.attempts == 2
    assert step_result.attempt_results[0].success is False
    assert step_result.attempt_results[1].success is True

    # scenario.scenario_2
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "scenario_2"
    ][0]
    assert step_result.success is True
    assert step_result.attempts == 1
    assert step_result.attempt_results[0].success is True

    # teardown
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "teardown"
    ][0]
    assert step_result.success is True
    assert step_result.attempts == 1
    assert step_result.attempt_results[0].success is True

    # global teardown
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "global_teardown"
    ][0]
    assert step_result.success is True
    assert step_result.attempts == 1
    assert step_result.attempt_results[0].success is True


@pytest.mark.artifact
@pytest.mark.retry
def test_artifact_failure_exhausts_retry(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then artifact failure exhausts retry.
    """
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
                    mock_artifact_step("scenario_1", tmp_path / "test_file.txt"),
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
                        path=tmp_path / "test_file.txt",
                        after_step="scenario_1",
                        retry_on_failure=True,
                    ),
                ]
            ),
        ),
    )

    runner = DeviceTestRunner(
        executor=MockAlwaysPassExecutor(),
        artifact_manager=ArtifactManager(tmp_path),
        artifact_validator=MockAlwaysFailArtifactValidator(),
        failure_classifier=FailureClassifier(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    # global setup
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "global_setup"
    ][0]
    assert step_result.attempts == 1

    # setup
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "setup"
    ][0]
    assert step_result.attempts == 1

    # scenario.scenario_1
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "scenario_1"
    ][0]
    assert step_result.attempts == 3
    assert step_result.success is False
    assert all(not attempt.success for attempt in step_result.attempt_results)

    # scenario.scenario_2
    # skip

    # scenario.teardown
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "teardown"
    ][0]
    assert step_result.attempts == 1

    # scenario.global_teardown
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "global_teardown"
    ][0]
    assert step_result.attempts == 1

    assert result.summary.status == "FAILED"


@pytest.mark.artifact
@pytest.mark.retry
def test_non_retryable_artifact_failure_doew_not_retry(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then non retryable artifact failure does not retry.
    """

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
                    mock_artifact_step("scenario_1", tmp_path / "test_file.txt"),
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
                        path=tmp_path / "test_file.txt",
                        after_step="scenario_1",
                        retry_on_failure=False,
                    ),
                ]
            ),
        ),
    )

    runner = DeviceTestRunner(
        executor=MockAlwaysPassExecutor(),
        artifact_manager=ArtifactManager(output_dir=tmp_path),
        artifact_validator=MockAlwaysFailArtifactValidator(),
        failure_classifier=FailureClassifier(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    # global setup
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "global_setup"
    ][0]
    assert step_result.attempts == 1

    # setup
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "setup"
    ][0]
    assert step_result.attempts == 1

    # scenario.scenario_1
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "scenario_1"
    ][0]
    assert step_result.attempts == 1

    # step 本身是 True
    assert step_result.success is True

    # scenario.scenario_2
    # skip

    # scenario.teardown
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "teardown"
    ][0]
    assert step_result.attempts == 1

    # scenario.global_teardown
    step_result = [
        step_result for step_result in result.step_results if step_result.name == "global_teardown"
    ][0]
    assert step_result.attempts == 1

    assert result.summary.status == "FAILED"

    # Final artifact validation 失敗
    assert result.summary.failed_artifact_rules == 1


@pytest.mark.artifact
@pytest.mark.retry
def test_retry_rules_are_filteredby_step(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then retry rules are filtered by step.
    """

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
                    mock_artifact_step("scenario_1", tmp_path / "test_file_1.txt"),
                    mock_artifact_step("scenario_2", tmp_path / "test_file_2.txt"),
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
                        name="test_file_1_exist",
                        type="exists",
                        path=tmp_path / "test_file_1.txt",
                        after_step="scenario_1",
                        retry_on_failure=True,
                    ),
                    ArtifactValidationRule(
                        name="test_file_2_exist",
                        type="exists",
                        path=tmp_path / "test_file_2.txt",
                        after_step="scenario_2",
                        retry_on_failure=True,
                    ),
                ]
            ),
        ),
    )

    rules = DeviceTestRunner._get_retry_rules_for_step(step_name="scenario_1", config=config)
    assert len(rules) == 1
    assert rules[0].name == "test_file_1_exist"

    rules = DeviceTestRunner._get_retry_rules_for_step(step_name="scenario_2", config=config)
    assert len(rules) == 1
    assert rules[0].name == "test_file_2_exist"


def test_artifact_missing_retries(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test lifecycle and its retry or artifact rules are configured.
    When the test runner executes the lifecycle.
    Then artifact missing causes another attempt while retry capacity remains.
    """

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
                    mock_artifact_step("scenario_1", tmp_path / "test_file.txt"),
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
                        path=tmp_path / "test_file.txt",
                        after_step="scenario_1",
                        retry_on_failure=True,
                    ),
                ]
            ),
        ),
    )

    executor = MockAlwaysPassExecutor()

    validator = MockMissingThenPassValidator()

    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=(ArtifactManager(tmp_path)),
        artifact_validator=validator,
        failure_classifier=(FailureClassifier()),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    # scenario_1
    step_result = result.step_results[2]

    assert step_result.attempts == 2

    assert step_result.attempt_results[0].failure_type == FailureType.ARTIFACT_MISSING
    assert step_result.attempt_results[1].failure_type == FailureType.NONE
    assert step_result.success is True
