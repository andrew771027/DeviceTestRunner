import json
from pathlib import Path

from runner.artifact_validator import ArtifactValidator
from runner.config import ConfigLoader
from runner.executor import SubprocessExecutor
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner

PROJECT_ROOT = Path(__file__).resolve().parent


def test_command_creates_and_validates_artifact(tmp_path: Path):
    output_dir = tmp_path / "artifacts"
    config_path = tmp_path / "config.yaml"

    config_path.write_text(
        f"""
    test_case:
        id: integration_001
        name: artifact integration test
        description: validate generate csv
    device:
        serial: fake_device
        product: fake_product
        build: fake_build
    lifecycle:
        global_setup:
            steps: []
        setup:
            steps:
              - name: create_results_directory
                type: command
                command: mkdir -p results
                timeout_second: 5
        scenario:
            steps:
              - name: create_result_csv
                type: command
                command: printf "Hello World" >> results/test_file.csv
                timeout_second: 5
        teardown:
            steps: []
        global_teardown:
            steps: []
    artifact:
        output_dir: {output_dir}
        validation:
            rules:
                - name: test_file_csv_exists
                  type: exists
                  path: results/test_file.csv
                - name: test_file_csv_size
                  type: file_size
                  path: results/test_file.csv
                  min_size_bytes: 10
                  max_size_bytes: 1000
                - name: test_file_csv_extension
                  type: file_extension
                  path: results/test_file.csv
                  allowed_extensions:
                    - csv
    """,
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_path)

    runner = DeviceTestRunner(
        executor=SubprocessExecutor(project_directory=PROJECT_ROOT),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    assert result.summary.status == "PASSED"

    assert result.summary.configured_steps == 2
    assert result.summary.executed_steps == 2
    assert result.summary.passed_steps == 2
    assert result.summary.skipped_steps == 0
    assert result.summary.failed_steps == 0

    assert result.summary.configured_artifact_rules == 3
    assert result.summary.passed_artifact_rules == 3
    assert result.summary.failed_artifact_rules == 0

    test_file = Path(result.artifact_dir) / "results" / "test_file.csv"

    assert test_file.exists()

    result_json = Path(result.artifact_dir) / "result.json"

    saved = json.loads(result_json.read_text(encoding="utf-8"))

    assert saved["summary"]["status"] == "PASSED"
    assert len(saved["artifact_validation_results"]) == 3
    assert all(item["passed"] for item in saved["artifact_validation_results"])


def test_run_fails_when_command_does_not_create_artifact(tmp_path: Path):
    output_dir = tmp_path / "artifacts"
    config_path = tmp_path / "config.yaml"

    config_path.write_text(
        f"""
    test_case:
        id: integration_missing
        name: missing artifact test
        description: command success but file is missing
    device:
        serial: fake_device
        product: fake_product
        build: fake_build
    lifecycle:
        global_setup:
            steps: []
        setup:
            steps: []
        scenario:
            steps:
                - name: successful_command
                  type: command
                  command: echo "scenario completed"
                  timeout_second: 5
        teardown:
            steps: []
        global_teardown:
            steps: []
    artifact:
        output_dir: {output_dir}
        validation:
            rules:
                - name: test_file_exist
                  type: exists
                  path: results/test_file.txt
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_path)
    runner = DeviceTestRunner(
        executor=SubprocessExecutor(project_directory=PROJECT_ROOT),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    assert result.summary.passed_steps == 1
    assert result.summary.failed_steps == 0

    assert result.summary.failed_artifact_rules == 1

    assert result.summary.status == "FAILED"

    validation = result.artifact_validation_results[0]

    assert validation.passed is False
    assert validation.message == "Artifact does not exist."


def test_command_runs_inside_run_directory(tmp_path: Path):
    output_dir = tmp_path / "artifacts"
    config_path = tmp_path / "config.yaml"

    config_path.write_text(
        f"""
    test_case:
        id: cwd_test
        name: CWD Test
        description: Verify command working directory
    device:
        serial: fake_device
        product: fake_product
        build: fake_build
    lifecycle:
        global_setup:
            steps: []
        setup:
            steps: []
        scenario:
            steps:
                - name: save_working_directory
                  type: command
                  command: pwd > current_directory.txt
                  timeout_seconds: 5
        teardown:
            steps: []
        global_teardown:
            steps: []
    artifact:
        output_dir: {output_dir}
        validaiton:
            rules:
                - name: cwd_file
                  type: existsa
                  path: current_directory.txt
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_path)
    runner = DeviceTestRunner(
        executor=SubprocessExecutor(PROJECT_ROOT),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    cwd_file = Path(result.artifact_dir) / "current_directory.txt"

    actual_directory = cwd_file.read_text(encoding="utf-8").strip()

    assert actual_directory == str(Path(result.artifact_dir).resolve())


def test_csv_and_json_content_validation(tmp_path: Path):
    output_dir = tmp_path / "artifacts"
    config_file = tmp_path / "config.yaml"

    config_file.write_text(
        f"""
    test_case:
        id: integration
        name: artifact content integration
        description: csv json validation
    device:
        serial: fake device
        product: fake_pixel
        build: fake_build
    lifecycle:
        global_setup:
            steps: []
        setup:
            steps:
            - name: create_results
              type: command
              command: mkdir -p results
              timeout_second: 5
        scenario:
            steps:
            - name: create_csv
              type: command
              command: |
                printf "timestamp,power\\n1,100\\n2,120\\n" > results/test_csv_file.csv
              timeout_second: 5
            - name: create_json
              type: command
              command: |
                printf '{{"status":"PASSED","metrics":{{"average_power":110.0,"sample_count":2}}}}' > results/test_json_file.json
              timeout_second: 5
        teardown:
            steps: []
        global_teardown:
            steps: []
    artifact:
        output_dir: {output_dir}
        validation:
            rules:
                - name: csv_content
                  type: csv_content
                  path: results/test_csv_file.csv
                  required_columns:
                    - timestamp
                    - power
                  min_rows: 2
                - name: json_content
                  type: json_content
                  path: results/test_json_file.json
                  required_json_paths:
                    - status
                    - metrics.average_power
                    - metrics.sample_count
                  expected_json_values:
                    status: PASSED
                    metrics.sample_count: 2
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_file)

    runner = DeviceTestRunner(
        executor=SubprocessExecutor(project_directory=PROJECT_ROOT),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    assert result.summary.status == "PASSED"
    assert result.summary.configured_artifact_rules == 2
    assert result.summary.passed_artifact_rules == 2
    assert result.summary.failed_artifact_rules == 0

    validaiton_results = result.artifact_validation_results

    assert len(validaiton_results) == 2
    assert validaiton_results[0].passed is True
    assert validaiton_results[1].passed is True

    saved_report = json.loads(
        (Path(result.artifact_dir) / "result.json").read_text(encoding="utf-8")
    )

    assert saved_report["metadata"]["runner_version"] == "1.4.1"
    assert saved_report["summary"]["status"] == "PASSED"


def test_run_fails_when_csv_content_invalid(tmp_path: Path):
    output_dir = tmp_path / "artifact"
    config_file = tmp_path / "config.yaml"

    config_file.write_text(
        f"""
        test_case:
            id: csv_failure
            name: CSV Failure
            description: Invalid CSV contract
        device:
            serial: fake_device
            product: fake_pixel
            build: fake_build
        lifecycle:
            global_setup:
                steps: []
            setup:
                steps: []
            scenario:
                steps:
                    - name: create_bad_csv
                      type: command
                      command: touch test_csv_file.csv
                      timeout_second: 5
            teardown:
                steps: []
            global_teardown:
                steps: []
        artifact:
            output_dir: {output_dir}
            validation:
                rules:
                    - name: csv_contract
                      type: csv_content
                      path: test_csv_file.csv
                      required_columns:
                        - timestamp
                        - power
                      min_rows: 1
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_file)
    runner = DeviceTestRunner(
        executor=SubprocessExecutor(project_directory=PROJECT_ROOT),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
        show_console_output=False,
    )
    result = runner.run(config)

    # step
    assert result.summary.configured_steps == 1
    assert result.summary.passed_steps == 1
    assert result.summary.failed_steps == 0
    assert result.summary.skipped_steps == 0

    # rule
    assert result.summary.passed_artifact_rules == 0
    assert result.summary.failed_artifact_rules == 1

    # run
    assert result.summary.status == "FAILED"

    validation = result.artifact_validation_results[0]

    assert validation.passed is False
    assert validation.message == "CSV header is missing."


def test_run_fails_when_json_status_invalid(tmp_path: Path):
    output_dir = tmp_path / "artifact"
    config_file = tmp_path / "config.yaml"

    config_file.write_text(
        f"""
        test_case:
            id: json_failure
            name: JSON Failure
            description: Invalid JSON result
        device:
            serial: fake_device
            product: fake_pixel
            build: fake_build
        lifecycle:
            global_setup:
                steps: []
            setup:
                steps: []
            scenario:
                steps:
                - name: create_json
                  type: command
                  command: |
                    printf '{{"status":"FAILED"}}' > test_json_file.json
                  timeout_second: 5
            teardown:
                steps: []
            global_teardown:
                steps: []
        artifact:
            output_dir: {output_dir}
            validation:
                rules:
                    - name: json_content
                      type: json_content
                      path: test_json_file.json
                      required_json_paths:
                        - status
                      expected_json_values:
                        status: PASSED

""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_file)
    runner = DeviceTestRunner(
        executor=SubprocessExecutor(project_directory=PROJECT_ROOT),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    assert result.summary.configured_steps == 1
    assert result.summary.passed_steps == 1
    assert result.summary.failed_steps == 0

    assert result.summary.passed_artifact_rules == 0
    assert result.summary.failed_artifact_rules == 1

    assert result.summary.status == "FAILED"
    assert "expected 'PASSED'" in result.artifact_validation_results[0].message
