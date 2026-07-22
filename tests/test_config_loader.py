from typing import List
from runner.config import ConfigLoader
from runner.models import (
    ArtifactConfig,
    DeviceInfo,
    DeviceTestCase,
    RunnerConfig,
    LifecycleSteps,
    LifecycleStepContent,
    LifecycleConfig,
)


def test_config_loader_loads_device_test_config(tmp_path):
    config_file = tmp_path / "sample.yaml"
    config_file.write_text(
        """
    test_case:
        id: hello_world_001
        name: hello_world
        description: this is hello world.
    device:
        serial: xxx001
        product: pixel
        build: 2026.xx.001

    lifecycle:
        global_setup:
            steps:
            - name: Hello World 1
              type: command
              command: "echo 'Hello World 1'"
              timeout_second: 1
        setup:
            steps:
            - name: Hello World 2
              type: command
              command: "echo 'Hello World 2'"
              timeout_second: 1
        scenario:
            steps:
            - name: Hello World 3
              type: command
              command: "echo 'Hello World 3'"
              timeout_second: 1
            - name: Hello World 4
              type: command
              command: "echo 'Hello World 4'"
              timeout_second: 1
        teardown:
            steps:
            - name: Hello World 5
              type: command
              command: "echo 'Hello World 5'"
              timeout_second: 1
        global_teardown:
            steps:
            - name: Hello World 6
              type: command
              command: "echo 'Hello World 6'"
              timeout_second: 1
    artifact:
        output_dir: artufact/hello_world
""",
        encoding="utf-8",
    )

    loader = ConfigLoader()
    config = loader.load(str(config_file))

    assert isinstance(config, RunnerConfig)
    assert isinstance(config.test_case, DeviceTestCase)
    assert config.test_case.id == "hello_world_001"
    assert config.test_case.name == "hello_world"
    assert config.test_case.description == "this is hello world."

    assert isinstance(config.device, DeviceInfo)
    assert config.device.serial == "xxx001"
    assert config.device.product == "pixel"
    assert config.device.build == "2026.xx.001"

    assert isinstance(config.lifecycle, LifecycleConfig)

    assert len(config.lifecycle.global_setup.steps) == 1
    assert isinstance(config.lifecycle.global_setup, LifecycleSteps)
    assert isinstance(config.lifecycle.global_setup.steps, list)
    assert isinstance(config.lifecycle.global_setup.steps[0], LifecycleStepContent)
    assert config.lifecycle.global_setup.steps[0].name == "Hello World 1"
    assert config.lifecycle.global_setup.steps[0].command == "echo 'Hello World 1'"

    assert len(config.lifecycle.setup.steps) == 1
    assert isinstance(config.lifecycle.setup, LifecycleSteps)
    assert isinstance(config.lifecycle.setup.steps, list)
    assert isinstance(config.lifecycle.setup.steps[0], LifecycleStepContent)
    assert config.lifecycle.setup.steps[0].name == "Hello World 2"
    assert config.lifecycle.setup.steps[0].command == "echo 'Hello World 2'"

    assert len(config.lifecycle.scenario.steps) == 2
    assert isinstance(config.lifecycle.scenario.steps, list)
    assert isinstance(config.lifecycle.scenario.steps[0], LifecycleStepContent)
    assert config.lifecycle.scenario.steps[0].name == "Hello World 3"
    assert config.lifecycle.scenario.steps[0].command == "echo 'Hello World 3'"
    assert isinstance(config.lifecycle.scenario.steps[1], LifecycleStepContent)
    assert config.lifecycle.scenario.steps[1].name == "Hello World 4"
    assert config.lifecycle.scenario.steps[1].command == "echo 'Hello World 4'"

    assert len(config.lifecycle.teardown.steps) == 1
    assert isinstance(config.lifecycle.teardown.steps, list)
    assert isinstance(config.lifecycle.teardown.steps[0], LifecycleStepContent)
    assert config.lifecycle.teardown.steps[0].name == "Hello World 5"
    assert config.lifecycle.teardown.steps[0].command == "echo 'Hello World 5'"

    assert len(config.lifecycle.global_teardown.steps) == 1
    assert isinstance(config.lifecycle.global_teardown.steps, list)
    assert isinstance(config.lifecycle.global_teardown.steps[0], LifecycleStepContent)
    assert config.lifecycle.global_teardown.steps[0].name == "Hello World 6"
    assert config.lifecycle.global_teardown.steps[0].command == "echo 'Hello World 6'"
    
    assert isinstance(config.artifact, ArtifactConfig)
    assert config.artifact.output_dir == "artufact/hello_world"
