from pathlib import Path

from runner.artifact import ArtifactManager
from runner.artifact_validator import ArtifactValidator
from runner.config import ConfigLoader
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner

PROJECT_ROOT = Path(__file__).resolve().parent


def test_real_artifact_aware_retry(tmp_path: Path):
    """Acceptance scenario.

    Given a real command initially produces an unacceptable artifact and retry is enabled.
    When the runner validates the artifact and performs the configured retry flow.
    Then the invalid first artifact triggers one retry and the corrected artifact allows the run to pass.
    """
    output_dir = tmp_path / "artifacts"

    config_file = tmp_path / "config.yaml"

    config_file.write_text(
        f"""
    test_case:
        id: artifact_retry
        name: Artifact Retry
        description: Retry invalid CSV
    device:
        serial: fake_serial,
        product: fake_pixel,
        build: fake_build,
    retry:
        max_attempts: 3
        delay_seconds: 0
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
                - name: run_power_test
                  type: command
                  command: |
                      COUNT_FILE=retry_count.txt

                      if [ ! -f "$COUNT_FILE" ]; then
                        echo 0 > "$COUNT_FILE"
                      fi

                      COUNT=$(cat "$COUNT_FILE")
                      COUNT=$((COUNT + 1))
                      echo "$COUNT" > "$COUNT_FILE"

                      if [ "$COUNT" -eq 1 ]; then
                        printf "timestamp,voltage\\n1,4.2\\n" \
                          > results/power.csv
                        exit 0
                      fi

                      printf "timestamp,power\\n1,100\\n2,120\\n" \
                        > results/power.csv

                      exit 0
                  timeout_second: 5
        teardown:
            steps: []
        global_teardown:
            steps: []
    artifact:
        output_dir: {output_dir}
        validation:
            rules:
              - name: power_csv
                type: csv_content
                path: results/power.csv
                after_step: run_power_test
                retry_on_failure: true
                required_columns:
                  - timestamp
                  - power
                min_rows: 2

""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_file)
    runner = DeviceTestRunner(
        executor=SubprocessExecutor(
            project_directory=PROJECT_ROOT,
            failure_classifier=FailureClassifier(),
        ),
        artifact_manager=ArtifactManager(output_dir=output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    scenario_result = next(step for step in result.step_results if step.name == "run_power_test")

    assert scenario_result.attempts == 2

    # attempt 1:
    # process PASS, artifact FAIL
    first_attempt = scenario_result.attempt_results[0]

    assert first_attempt.exit_code == 0
    assert first_attempt.success is False
    assert first_attempt.artifact_validation_results[0].passed is False

    # attempt 2:
    # process PASS, artifact PASS
    second_attempt = scenario_result.attempt_results[1]

    assert second_attempt.exit_code == 0
    assert second_attempt.success is True
    assert second_attempt.artifact_validation_results[0].passed is True

    assert result.summary.status == "PASSED"
