from pathlib import Path

from runner.config import ConfigLoader
from runner.models import (
    ArtifactConfig,
    DeviceInfo,
    DeviceTestCase,
    LifecycleConfig,
    LifecycleStepContent,
    LifecycleSteps,
    RunnerConfig,
)


def test_config_loader_loads_device_test_config(tmp_path: Path):
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


def test_load_artifact_validation_config(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
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
            steps: []
        setup:
            steps: []
        scenario:
            steps: []
        teardown:
            steps: []
        global_teardown:
            steps: []
    artifact:
        output_dir: artufact/hello_world
        validation:
            rules:
                - name: result_exists
                  type: exists
                  path: result.txt
                - name: result_size
                  type: file_size
                  path: result.txt
                  min_size_bytes: 100
                  max_size_bytes: 1000
                - name: result_extension
                  type: file_extension
                  path: result.txt
                  allowed_extensions:
                    - csv
                    - txt
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_file)

    rules = config.artifact.validation.rules

    assert len(rules) == 3

    assert rules[0].name == "result_exists"
    assert rules[0].type == "exists"
    assert rules[0].path == "result.txt"

    assert rules[1].name == "result_size"
    assert rules[1].type == "file_size"
    assert rules[1].path == "result.txt"
    assert rules[1].min_size_bytes == 100
    assert rules[1].max_size_bytes == 1000

    assert rules[2].name == "result_extension"
    assert rules[2].type == "file_extension"
    assert sorted(rules[2].allowed_extensions) == sorted(["txt", "csv"])


def test_artifact_validation_is_optional(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
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

    assert config.artifact.validation.rules == []

def test_load_csv_and_json_validation_rules(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
   test_case: 
    id: power_001 
    name: Power Test 
    description: Content validation 
   device: 
    serial: fake 
    product: pixel 
    build: build_001 
   lifecycle: 
    global_setup: 
        steps: [] 
    setup: 
        steps: [] 
    scenario: 
        steps: [] 
    teardown: 
        steps: [] 
    global_teardown: 
        steps: [] 
   artifact: 
    output_dir: artifacts 
    validation: 
        rules: 
        - name: csv_rule 
          type: csv_content 
          path: results/power.csv 
          required_columns: 
          - timestamp 
          - power 
          min_rows: 10 
        - name: json_rule 
          type: json_content 
          path: results/result.json 
          required_json_paths: 
            - status 
            - metrics.average_power 
          expected_json_values: 
            status: PASSED 
            metrics.sample_count: 100 
""", encoding="utf-8"
    )

    config = ConfigLoader().load(config_file)

    rules = config.artifact.validation.rules

    csv_rule = rules[0]
    assert csv_rule.type == "csv_content"
    assert csv_rule.required_columns == ["timestamp", "power"]
    assert csv_rule.min_rows == 10

    json_rule = rules[1]
    assert json_rule.type == "json_content"
    assert json_rule.required_json_paths == ["status", "metrics.average_power"]
    assert json_rule.expected_json_values["status"] == "PASSED"
    assert json_rule.expected_json_values["metrics"]["sample_count"] == 100