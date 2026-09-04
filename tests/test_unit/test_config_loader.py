from pathlib import Path

import pytest

from runner.config import ConfigLoader
from runner.models import (
    ArtifactConfig,
    DeviceInfo,
    DeviceTestCase,
    FailureType,
    LifecycleConfig,
    LifecycleStepContent,
    LifecycleSteps,
    RunnerConfig,
)


def test_config_loader_loads_device_test_config(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test YAML configuration defines the requested options.
    When the runner configuration is loaded.
    Then config loader loads device test config.
    """
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
    """Acceptance scenario.

    Given a device-test YAML configuration defines the requested options.
    When the runner configuration is loaded.
    Then load artifact validation config.
    """
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
    """Acceptance scenario.

    Given a device-test YAML configuration defines the requested options.
    When the runner configuration is loaded.
    Then artifact validation is optional.
    """
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


def test_artifact_retry_defaults_to_false(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test YAML configuration defines the requested options.
    When the runner configuration is loaded.
    Then artifact retry defaults to false.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
    test_case:
        id: retry_001
        name: Retry Test
        description: retry
    device:
        serial: fake_serial
        product: fake_pixel
        build: fake_build
    retry:
        max_attempts: 3
        delay_seconds: 1
    lifecycle:
        global_setup:
            steps: []
        setup:
            steps:
            - name: run_power_test
              type: command
              command: echo test
              timeout_second: 5
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
                - name: csv_content
                  type: csv_content
                  path: results/power.csv
                  required: False
                  required_columns:
                    - timestamp
                    - power
                  min_rows: 10
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_file)
    rule = config.artifact.validation.rules[0]

    assert rule.after_step is None
    assert rule.required is False


def test_load_csv_and_json_validation_rules(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test YAML configuration defines the requested options.
    When the runner configuration is loaded.
    Then load CSV and JSON validation rules.
    """
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
        steps:
        - name: create_csv
          type: command
          command: |
            printf "timestamp,power\\n1,100\\n2,120\\n" > test_csv_file.csv
          timeout_second: 5
        - name: create_json
          type: command
          command: |
            printf '{{"status":"PASSED","metrics":{{"average_power":110.0,"sample_count":2}}}}' > test_json_file.json
          timeout_second: 5
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
          path: test_csv_file.csv
          required_columns:
          - timestamp
          - power
          min_rows: 2
        - name: json_rule
          type: json_content
          path: test_json_file.json
          required_json_paths:
            - status
            - metrics.average_power
          expected_json_values:
            status: PASSED
            metrics.sample_count: 100
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_file)

    rules = config.artifact.validation.rules

    csv_rule = rules[0]
    assert csv_rule.type == "csv_content"
    assert csv_rule.required_columns == ["timestamp", "power"]
    assert csv_rule.min_rows == 2

    json_rule = rules[1]
    assert json_rule.type == "json_content"
    assert json_rule.required_json_paths == ["status", "metrics.average_power"]
    assert json_rule.expected_json_values["status"] == "PASSED"
    assert json_rule.expected_json_values["metrics.sample_count"] == 100


def test_load_retry_config(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test YAML configuration defines the requested options.
    When the runner configuration is loaded.
    Then load retry config.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
    test_case:
        id: retry_001
        name: Retry Test
        description: retry
    device:
        serial: fake_serial
        product: fake_pixel
        build: fake_build
    retry:
        max_attempts: 3
        delay_seconds: 3
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
""",
        encoding="UTF-8",
    )

    config = ConfigLoader().load(config_file)

    assert hasattr(config, "retry")
    assert config.retry.max_attempts == 3
    assert config.retry.delay_seconds == 3


def test_load_artifact_aware_retry_rule(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test YAML configuration defines the requested options.
    When the runner configuration is loaded.
    Then load artifact aware retry rule.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
    test_case:
        id: retry_001
        name: Retry Test
        description: retry
    device:
        serial: fake_serial
        product: fake_pixel
        build: fake_build
    retry:
        max_attempts: 3
        delay_seconds: 1
    lifecycle:
        global_setup:
            steps: []
        setup:
            steps:
            - name: run_power_test
              type: command
              command: echo test
              timeout_second: 5
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
                - name: csv_content
                  type: csv_content
                  path: results/power.csv
                  after_step: run_power_test
                  required: true
                  required_columns:
                    - timestamp
                    - power
                  min_rows: 10
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_file)
    rule = config.artifact.validation.rules[0]

    assert rule.after_step == "run_power_test"
    assert rule.required is True
    assert rule.required_columns == ["timestamp", "power"]
    assert rule.min_rows == 10


def test_retry_config_uses_default_values(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test YAML configuration defines the requested options.
    When the runner configuration is loaded.
    Then retry config uses default values.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
       test_case:
           id: retry_001
           name: Retry Test
           description: retry
       device:
           serial: fake_serial
           product: fake_pixel
           build: fake_build
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
   """,
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_file)

    assert config.retry.max_attempts == 1
    assert config.retry.delay_seconds == 0


def test_retry_max_attempts_must_be_positive(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test YAML configuration defines the requested options.
    When the runner configuration is loaded.
    Then retry max attempts must be positive.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
       test_case:
           id: retry_001
           name: Retry Test
           description: retry
       device:
           serial: fake_serial
           product: fake_pixel
           build: fake_build
       retry:
           max_attempts: -10
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
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=("retry.max_attempts must be >= 1")):
        ConfigLoader().load(config_file)


def test_retry_delay_seconds_must_be_positive(tmp_path: Path):
    """Acceptance scenario.

    Given a device-test YAML configuration defines the requested options.
    When the runner configuration is loaded.
    Then retry delay seconds must be positive.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
       test_case:
           id: retry_001
           name: Retry Test
           description: retry
       device:
           serial: fake_serial
           product: fake_pixel
           build: fake_build
       retry:
           delay_seconds: -10
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
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=("retry.delay_seconds must be >= 0")):
        ConfigLoader().load(config_file)


def test_artifact_required_defaults_to_true():
    """Acceptance scenario.

    Given an artifact validation rule omits the required option.
    When artifact configuration is loaded.
    Then the rule defaults to required.
    """

    raw = {"validation": {"rules": [{"name": "test", "type": "exists", "path": "test.csv"}]}}

    config = ConfigLoader._load_artifact_validation(raw)

    assert config.rules[0].required is True


def test_load_optional_artifact():
    """Acceptance scenario.

    Given an artifact validation rule explicitly sets required to false.
    When artifact configuration is loaded.
    Then the rule is preserved as optional.
    """

    raw = {
        "validation": {
            "rules": [
                {
                    "name": "debug_log",
                    "type": "exists",
                    "path": "debug.log",
                    "required": False,
                }
            ]
        }
    }

    config = ConfigLoader._load_artifact_validation(raw)

    assert config.rules[0].required is False


def test_build_selective_retry_config():
    """Acceptance scenario.

    Given retry configuration lists supported failure types.
    When retry configuration is loaded.
    Then timing values and ordered failure types are preserved.
    """

    raw = {
        "retry": {
            "max_attempts": 3,
            "delay_seconds": 2,
            "retry_on": [
                "timeout",
                "device_offline",
                "artifact_missing",
            ],
        }
    }

    config = ConfigLoader._load_retry(raw)

    assert config.max_attempts == 3
    assert config.delay_seconds == 2

    assert config.retry_on == [
        FailureType.TIMEOUT,
        FailureType.DEVICE_OFFLINE,
        FailureType.ARTIFACT_MISSING,
    ]


def test_retry_on_defaults_to_empty():
    """Acceptance scenario.

    Given retry configuration omits retry_on.
    When retry configuration is loaded.
    Then no failure type is eligible for retry.
    """

    raw = {"retry": {"max_attempts": 3}}

    config = ConfigLoader._load_retry(raw)

    assert config.max_attempts == 3
    assert config.retry_on == []


def test_unknown_retry_failure_type_raises_value_error():
    """Acceptance scenario.

    Given retry_on contains an unknown failure type.
    When the failure type list is parsed.
    Then configuration is rejected with a ValueError.
    """
    with pytest.raises(ValueError, match="retry failure type: unknown"):
        ConfigLoader._parse_retry_on(["unknown"])


def test_retry_on_rejects_none():
    """Acceptance scenario.

    Given retry_on contains the successful none classification.
    When the failure type list is parsed.
    Then configuration is rejected because success cannot be retried.
    """
    with pytest.raises(ValueError, match="cannot contain 'none"):
        ConfigLoader._parse_retry_on(["none"])


def test_duplicate_retry_on_values_are_removed():
    """Acceptance scenario.

    Given retry_on repeats a supported failure type.
    When the failure type list is parsed.
    Then duplicates are removed while the original order is retained.
    """
    retry_on = ConfigLoader._parse_retry_on(
        ["timeout", "device_offline", "timeout", "artifact_missing"]
    )

    assert retry_on == [
        FailureType.TIMEOUT,
        FailureType.DEVICE_OFFLINE,
        FailureType.ARTIFACT_MISSING,
    ]
