import pytest

from runner.models import (
    ArtifactConfig,
    ArtifactValidationConfig,
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
    StepResult,
)


@pytest.mark.parametrize(
    argnames="config",
    argvalues=[
        RunnerConfig(
            test_case=DeviceTestCase(
                id="power_001",
                name="test all section",
                description="This is the test case to test all sections are well config",
            ),
            device=DeviceInfo(
                serial="emulator-5566",
                product="pixel",
                build="2026.08.01.001",
            ),
            lifecycle=LifecycleConfig(
                global_setup=LifecycleSteps(
                    [
                        LifecycleStepContent(
                            name="clear_process",
                            type="command",
                            command="bash scripts/clear_process.sh",
                            timeout_second=10,
                        ),
                    ]
                ),
                setup=LifecycleSteps(
                    [
                        LifecycleStepContent(
                            name="setup_device",
                            type="command",
                            command="bash scripts/setup_script.sh",
                            timeout_second=10,
                        ),
                    ]
                ),
                scenario=LifecycleSteps(
                    [
                        LifecycleStepContent(
                            name="run_scenario",
                            type="command",
                            command="bash scripts/run_scenario.sh",
                            timeout_second=10,
                        ),
                    ]
                ),
                teardown=LifecycleSteps(
                    [
                        LifecycleStepContent(
                            name="teardown_device",
                            type="command",
                            command="bash scripts/teardown_script.sh",
                            timeout_second=10,
                        ),
                    ]
                ),
                global_teardown=LifecycleSteps(
                    [
                        LifecycleStepContent(
                            name="cleanup",
                            type="command",
                            command="bash scripts/cleanup.sh",
                            timeout_second=10,
                        ),
                    ]
                ),
            ),
            retry=RetryConfig(
                max_attempts=3,
                delay_seconds=1,
            ),
            artifact=ArtifactConfig(
                output_dir="artifact/sample_device_config",
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
                            min_size_bytes=1,
                            max_size_bytes=100,
                        ),
                    ]
                ),
            ),
        )
    ],
)
def test_config_contains_all_section(config: RunnerConfig):
    """Acceptance scenario.

    Given runner model data is constructed from test configuration or execution results.
    When the model exposes its derived state.
    Then every configured lifecycle section and test-case field is represented by the runner model.
    """

    assert config.test_case.id == "power_001"
    assert config.test_case.name == "test all section"
    assert (
        config.test_case.description == "This is the test case to test all sections are well config"
    )

    assert config.device.serial == "emulator-5566"
    assert config.device.product == "pixel"
    assert config.device.build == "2026.08.01.001"

    assert len(config.lifecycle.global_setup.steps) == 1
    assert config.lifecycle.global_setup.steps[0].name == "clear_process"
    assert config.lifecycle.global_setup.steps[0].type == "command"
    assert config.lifecycle.global_setup.steps[0].command == "bash scripts/clear_process.sh"
    assert config.lifecycle.global_setup.steps[0].timeout_second == 10

    assert len(config.lifecycle.setup.steps) == 1
    assert config.lifecycle.setup.steps[0].name == "setup_device"
    assert config.lifecycle.setup.steps[0].type == "command"
    assert config.lifecycle.setup.steps[0].command == "bash scripts/setup_script.sh"
    assert config.lifecycle.setup.steps[0].timeout_second == 10

    assert len(config.lifecycle.scenario.steps) == 1
    assert config.lifecycle.scenario.steps[0].name == "run_scenario"
    assert config.lifecycle.scenario.steps[0].type == "command"
    assert config.lifecycle.scenario.steps[0].command == "bash scripts/run_scenario.sh"
    assert config.lifecycle.scenario.steps[0].timeout_second == 10

    assert len(config.lifecycle.teardown.steps) == 1
    assert config.lifecycle.teardown.steps[0].name == "teardown_device"
    assert config.lifecycle.teardown.steps[0].type == "command"
    assert config.lifecycle.teardown.steps[0].command == "bash scripts/teardown_script.sh"
    assert config.lifecycle.teardown.steps[0].timeout_second == 10

    assert len(config.lifecycle.global_teardown.steps) == 1
    assert config.lifecycle.global_teardown.steps[0].name == "cleanup"
    assert config.lifecycle.global_teardown.steps[0].type == "command"
    assert config.lifecycle.global_teardown.steps[0].command == "bash scripts/cleanup.sh"
    assert config.lifecycle.global_teardown.steps[0].timeout_second == 10

    assert hasattr(config.artifact, "output_dir")
    assert config.artifact.output_dir == "artifact/sample_device_config"

    assert hasattr(config.artifact, "validation")
    assert len(config.artifact.validation.rules) == 2
    assert config.artifact.validation.rules[0].name == "test_file_exist"
    assert config.artifact.validation.rules[0].type == "exists"
    assert config.artifact.validation.rules[0].path == "results/test_file.txt"

    assert config.artifact.validation.rules[1].name == "test_file_size"
    assert config.artifact.validation.rules[1].type == "file_size"
    assert config.artifact.validation.rules[1].path == "results/test_file.txt"
    assert config.artifact.validation.rules[1].min_size_bytes == 1
    assert config.artifact.validation.rules[1].max_size_bytes == 100


@pytest.mark.parametrize(
    argnames="result",
    argvalues=[
        StepResult(
            stage="test_stage",
            name="test_step",
            command="echo 'Hello World'",
            attempts=1,
            success=True,
            attempt_results=[
                StepAttemptResult(
                    attempt=1,
                    success=True,
                    failure_type=FailureType.NONE,
                    exit_code=0,
                    duration_seconds=1,
                    stdout="",
                    stderr="",
                    stdout_log_path="",
                    stderr_log_path="",
                    error="",
                )
            ],
            duration_seconds=1,
        ),
    ],
)
def test_step_result_passed_when_exit_code_is_zero(result):
    """Acceptance scenario.

    Given runner model data is constructed from test configuration or execution results.
    When the model exposes its derived state.
    Then step result passed when exit code is zero.
    """
    assert result.success is True


@pytest.mark.parametrize(
    argnames="result",
    argvalues=[
        StepResult(
            stage="test_stage",
            name="test_step",
            command="echo 'Hello World'",
            attempts=1,
            success=False,
            attempt_results=[
                StepAttemptResult(
                    attempt=1,
                    success=False,
                    failure_type=FailureType.PROCESS_ERROR,
                    exit_code=1,
                    duration_seconds=1,
                    stdout="",
                    stderr="",
                    stdout_log_path="",
                    stderr_log_path="",
                    error="",
                )
            ],
            duration_seconds=1,
        )
    ],
)
def test_step_result_failed_when_exit_code_is_not_zero(result):
    """Acceptance scenario.

    Given runner model data is constructed from test configuration or execution results.
    When the model exposes its derived state.
    Then step result failed when exit code is not zero.
    """
    assert result.success is False
