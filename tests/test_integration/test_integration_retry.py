import os
import sys
import time
from pathlib import Path

from runner.artifact import ArtifactManager
from runner.artifact_validator import ArtifactValidator
from runner.cancellation import CancellationToken
from runner.config import ConfigLoader
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.models import (
    ArtifactConfig,
    DeviceInfo,
    DeviceTestCase,
    FailureType,
    LifecycleConfig,
    LifecycleStepContent,
    LifecycleSteps,
    RetryConfig,
    RunnerConfig,
)
from runner.process import ProcessTerminator
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner

PROJECT_ROOT = Path(__file__).resolve().parent


def is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)

    except ProcessLookupError:
        return False

    except PermissionError:
        #
        # Process 存在
        # 只是目前沒有權限 singnal
        #
        return True
    return True


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
        retry_on:
            - artifact_invalid
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
                required: true
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
            process_terminator=ProcessTerminator(),
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


def test_retry_does_not_leave_previous_attempt_process(tmp_path: Path):

    #
    # ------------------------------------------------
    # Project root
    # ------------------------------------------------
    #

    """Acceptance scenario.

    Given the first real attempt starts a child and exceeds its timeout.
    When the runner retries the step.
    Then attempt two verifies both previous PIDs are absent before succeeding.
    """
    project_root = Path(__file__).resolve().parents[2]

    fixture_script = project_root / "tests" / "fixtures" / "retry_process.py"

    assert fixture_script.exists()

    #
    # 使用目前 pytest 所使用的 python
    #
    # 比直接寫 python 更穩定
    command = f'"{sys.executable}" "{fixture_script}"'

    #
    # ------------------------------------------
    # Config
    # ------------------------------------------
    #
    config = RunnerConfig(
        test_case=DeviceTestCase(
            id="retry_process_test",
            name="retry_process_test",
            description=("Verify process cleanup before retry"),
        ),
        device=DeviceInfo(serial="device_001", product="pixel", build="build_001"),
        retry=RetryConfig(max_attempts=2, delay_seconds=0.01, retry_on=[FailureType.TIMEOUT]),
        lifecycle=LifecycleConfig(
            global_setup=LifecycleSteps(steps=[]),
            setup=LifecycleSteps(steps=[]),
            scenario=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="retry_process",
                        type="command",
                        command=command,
                        #
                        # Attempt 1 sleep 30 sec
                        # 所以一定會timeout
                        #
                        timeout_second=1,
                    )
                ]
            ),
            teardown=LifecycleSteps(steps=[]),
            global_teardown=LifecycleSteps(steps=[]),
        ),
        artifact=ArtifactConfig(output_dir=str(tmp_path)),
    )

    #
    # --------------------------------------
    # Real Executor
    # --------------------------------------
    #

    failure_classifier = FailureClassifier()

    process_terminator = ProcessTerminator(grace_period_seconds=0.5, poll_interval_seconds=0.05)

    executor = SubprocessExecutor(
        project_directory=project_root,
        failure_classifier=failure_classifier,
        process_terminator=process_terminator,
    )

    artifact_manager = ArtifactManager(tmp_path)

    runner = DeviceTestRunner(
        executor=executor,
        artifact_manager=artifact_manager,
        artifact_validator=ArtifactValidator(),
        failure_classifier=failure_classifier,
        reporter=JsonReporter(),
        show_console_output=False,
    )

    #
    # --------------------------------------------
    # Run
    # --------------------------------------------
    #

    result = runner.run(config=config, cancellation_token=CancellationToken())

    #
    # --------------------------------------------
    # Find scenario result
    # --------------------------------------------
    #
    scenario_result = next(
        step_result for step_result in result.step_results if (step_result.name == "retry_process")
    )

    #
    # ------------------------------------------
    # Retry Assertions
    # ------------------------------------------
    #

    assert scenario_result.attempts == 2
    assert scenario_result.success is True
    assert scenario_result.cancelled is False
    assert len(scenario_result.attempt_results) == 2

    #
    # Attempt 1
    #

    attempt_1 = scenario_result.attempt_results[0]
    assert attempt_1.success is False
    assert attempt_1.timed_out is True
    assert attempt_1.cancelled is False
    assert attempt_1.failure_type == FailureType.TIMEOUT

    #
    # Attempt 2
    #

    attempt_2 = scenario_result.attempt_results[1]
    assert attempt_2.success is True
    assert attempt_2.timed_out is False
    assert attempt_2.cancelled is False
    assert attempt_2.failure_type == FailureType.NONE

    assert "attempt 2 success" in attempt_2.stdout
    assert "previous attempt tree cleaned before retry" in attempt_2.stdout

    #
    # -----------------------------------------
    # Find run directory
    # -----------------------------------------
    #
    # RunResult.artifact_dir 是此次執行的結果目錄。
    #

    assert result.artifact_dir is not None
    run_dir = Path(result.artifact_dir)

    pid_file = run_dir / "attempt_1.pid"

    assert pid_file.exists()

    attempt_1_pid = int(pid_file.read_text(encoding="utf-8").strip())

    #
    # -----------------------------------------
    # Critical assertion
    # -----------------------------------------
    #
    # Executor 在 Attempt 1 return 前
    # 應該已經把 process 收乾淨。
    #

    deadline = time.monotonic() + 1.0

    while is_process_alive(attempt_1_pid) and time.monotonic() < deadline:

        time.sleep(0.05)

    assert is_process_alive(attempt_1_pid) is False
