from runner.models import (
    ArtifactConfig,
    DeviceInfo,
    DeviceTestCase,
    RunnerConfig,
    StepResult,
    Workflow,
    WorkflowStep,
)


def test_config_contains_all_section():
    config = RunnerConfig(
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
        workflow=Workflow(
            steps=[
                WorkflowStep(
                    name="setup_device",
                    type="command",
                    command="bash scripts/setup_script.sh",
                    timeout_second=10,
                ),
                WorkflowStep(
                    name="run_scenario",
                    type="command",
                    command="bash scripts/run_scenario.sh",
                    timeout_second=10,
                ),
            ],
        ),
        artifact=ArtifactConfig(output_dir="artifact/sample_device_config"),
    )

    assert config.test_case.id == "power_001"
    assert config.test_case.name == "test all section"
    assert (
        config.test_case.description == "This is the test case to test all sections are well config"
    )

    assert config.device.serial == "emulator-5566"
    assert config.device.product == "pixel"
    assert config.device.build == "2026.08.01.001"

    assert len(config.workflow.steps) == 2
    assert config.workflow.steps[0].name == "setup_device"
    assert config.workflow.steps[0].type == "command"
    assert config.workflow.steps[0].command == "bash scripts/setup_script.sh"
    assert config.workflow.steps[0].timeout_second == 10

    assert config.workflow.steps[1].name == "run_scenario"
    assert config.workflow.steps[1].type == "command"
    assert config.workflow.steps[1].command == "bash scripts/run_scenario.sh"
    assert config.workflow.steps[1].timeout_second == 10

    assert config.artifact.output_dir == "artifact/sample_device_config"


def test_step_result_passed_when_exit_code_is_zero():
    result = StepResult(
        step_name="setup_device",
        command="bash scripts/setup_script.sh",
        success=True,
        exit_code=0,
        duration_seconds=1,
        stderr="",
        stdout="",
        error=None,
    )

    assert result.passed is True


def test_step_result_failed_when_exit_code_is_not_zero():
    result = StepResult(
        step_name="setup_device",
        command="bash scripts/setup_script.sh",
        success=False,
        exit_code=1,
        duration_seconds=1,
        stderr="",
        stdout="",
        error=None,
    )

    assert result.passed is False
