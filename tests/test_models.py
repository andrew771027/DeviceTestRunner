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
            artifact=ArtifactConfig(output_dir="artifact/sample_device_config"),
        )
    ],
)
def test_config_contains_all_section(config: RunnerConfig):

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

    assert config.artifact.output_dir == "artifact/sample_device_config"


@pytest.mark.parametrize(
    argnames="result",
    argvalues=[
        StepResult(
            stage="test_stage",
            name="test_step",
            command="echo 'Hello World'",
            success=True,
            exit_code=0,
            duration_seconds=1,
            stderr="",
            stdout="",
            error=None,
        ),
    ],
)
def test_step_result_passed_when_exit_code_is_zero(result):
    assert result.passed is True


@pytest.mark.parametrize(
    argnames="result",
    argvalues=[
        StepResult(
            stage="test_stage",
            name="test_step",
            command="echo 'Hello World'",
            success=False,
            exit_code=1,
            duration_seconds=1,
            stderr="",
            stdout="",
            error=None,
        )
    ],
)
def test_step_result_failed_when_exit_code_is_not_zero(result):
    assert result.passed is False
