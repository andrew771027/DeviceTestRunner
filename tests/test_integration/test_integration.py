import json
from pathlib import Path

from runner.artifact import ArtifactManager
from runner.artifact_validator import ArtifactValidator
from runner.config import ConfigLoader
from runner.executor import SubprocessExecutor
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner

PROJECT_ROOT = Path(__file__).resolve().parent


def test_yaml_to_result_json(tmp_path):
    config_file = tmp_path / "intergration.yaml"
    config_file.write_text(
        """
test_case:
  id: power_003
  name: intergration_test
  description: This is integraiton test

device:
  serial: xxx_003
  product: product_003
  build: test_001

lifecycle:
  global_setup:
      steps:
      - name: global_setup
        type: command
        command: "echo 'Hello World'"
        timeout_second: 10
  setup:
      steps:
      - name: setup
        type: command
        command: "echo 'Hello World'"
        timeout_second: 5
  scenario:
      steps:
      - name: scenario_1
        type: command
        command: "echo 'Hello World'"
        timeout_second: 1
      - name: scenario_2
        type: command
        command: "echo 'Hello World'"
        timeout_second: 1
  teardown:
      steps:
      - name: teardown
        type: command
        command: "echo 'Hello World'"
        timeout_second: 1
  global_teardown:
      steps:
      - name: global_teardown
        type: command
        command: "echo 'Hello World'"
        timeout_second: 1


artifact:
  output_dir: "artifact/intergration_test"
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(str(config_file))
    runner = DeviceTestRunner(
        executor=SubprocessExecutor(project_directory=PROJECT_ROOT),
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
    )
    result = runner.run(config)

    assert result.metadata.test_case_name == "intergration_test"
    assert result.passed is True

    assert len(result.step_results) == 6

    assert result.summary.status == "PASSED"
    assert result.summary.executed_steps == 6

    step_result = result.step_results[0]
    latest_attempt = step_result.attempt_results[-1]
    assert latest_attempt.stdout == "Hello World\n"
    assert latest_attempt.stderr == ""

    stdout_path = Path(latest_attempt.stdout_log_path)
    stderr_path = Path(latest_attempt.stderr_log_path)

    assert stdout_path.exists()
    assert stderr_path.exists()

    assert stdout_path.read_text(encoding="utf-8") == latest_attempt.stdout
    assert stderr_path.read_text(encoding="utf-8") == latest_attempt.stderr

    assert result.step_results[0].name == "global_setup"
    assert "Hello World" in result.step_results[0].attempt_results[-1].stdout

    assert result.step_results[1].name == "setup"
    assert "Hello World" in result.step_results[1].attempt_results[-1].stdout

    assert result.step_results[2].name == "scenario_1"
    assert "Hello World" in result.step_results[2].attempt_results[-1].stdout

    assert result.step_results[3].name == "scenario_2"
    assert "Hello World" in result.step_results[3].attempt_results[-1].stdout

    assert result.step_results[4].name == "teardown"
    assert "Hello World" in result.step_results[4].attempt_results[-1].stdout

    assert result.step_results[5].name == "global_teardown"
    assert "Hello World" in result.step_results[5].attempt_results[-1].stdout

    assert "intergration_test" in result.metadata.test_case_name

    run_dir = Path(result.artifact_dir)
    assert run_dir.exists()
    assert (run_dir / "result.json").exists()

    scenario_stdout = run_dir / "scenario" / "scenario_1" / "attempt_1.stdout.log"
    assert scenario_stdout.exists()

    assert scenario_stdout.read_text(encoding="utf-8") == "Hello World\n"

    scenario_stdout = run_dir / "scenario" / "scenario_2" / "attempt_1.stdout.log"
    assert scenario_stdout.exists()

    assert scenario_stdout.read_text(encoding="utf-8") == "Hello World\n"

    report = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))

    assert report["metadata"]["runner_version"] == "1.5.1"

    assert report["summary"]["status"] == "PASSED"

    assert len(report["step_results"]) == 6


def test_integration_stops_after_failed_step(tmp_path):

    config_file = tmp_path / "intergration.yaml"
    config_file.write_text(
        """
test_case:
  id: power_003
  name: intergration_test
  description: This is integraiton test

device:
  serial: xxx_003
  product: product_003
  build: test_003

lifecycle:
  global_setup:
    steps:
      - name: global_setup
        type: command
        command: "echo 'Hello World'"
        timeout_second: 1
  setup:
    steps:
      - name: setup
        type: command
        command: "echo 'Hello World'"
        timeout_second: 1
  scenario:
      steps:
      - name: scenario_1
        type: command
        command: "echo 'Hello World'"
        timeout_second: 1
      - name: scenario_2
        type: command
        command: "exit 1"
        timeout_second: 1
  teardown:
    steps:
      - name: teardown
        type: command
        command: "echo 'Hello World'"
        timeout_second: 1
  global_teardown:
      steps:
      - name: global_teardown
        type: command
        command: "echo 'Hello World'"
        timeout_second: 1
artifact:
  output_dir: "artifact/intergration_test"
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_file)

    runner = DeviceTestRunner(
        executor=SubprocessExecutor(project_directory=PROJECT_ROOT),
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
    )

    result = runner.run(config)

    assert result.metadata.test_case_name == "intergration_test"
    assert result.passed is False

    assert len(result.step_results) == 6

    assert result.summary.status == "FAILED"
    assert result.summary.executed_steps == 6

    assert result.step_results[0].name == "global_setup"
    assert "Hello World" in result.step_results[0].attempt_results[-1].stdout

    assert result.step_results[1].name == "setup"
    assert "Hello World" in result.step_results[1].attempt_results[-1].stdout

    assert result.step_results[2].name == "scenario_1"
    assert "Hello World" in result.step_results[2].attempt_results[-1].stdout

    assert result.step_results[3].name == "scenario_2"
    assert result.step_results[3].attempt_results[-1].stdout == ""
    assert result.step_results[3].attempt_results[-1].stderr == ""
    assert result.step_results[3].attempt_results[-1].exit_code == 1

    failed_step_result = result.step_results[3]
    latest_attempt = failed_step_result.attempt_results[-1]
    assert latest_attempt.stdout == ""
    assert latest_attempt.stderr == ""

    stdout_path = Path(latest_attempt.stdout_log_path)
    stderr_path = Path(latest_attempt.stderr_log_path)

    assert stdout_path.exists()
    assert stderr_path.exists()

    assert stdout_path.read_text(encoding="utf-8") == latest_attempt.stdout
    assert stderr_path.read_text(encoding="utf-8") == latest_attempt.stderr

    assert result.step_results[4].name == "teardown"
    assert "Hello World" in result.step_results[4].attempt_results[-1].stdout

    assert result.step_results[5].name == "global_teardown"
    assert "Hello World" in result.step_results[5].attempt_results[-1].stdout

    assert "intergration_test" in result.metadata.test_case_name

    run_dir = Path(result.artifact_dir)
    assert run_dir.exists()
    assert (run_dir / "result.json").exists()

    scenario_stdout = run_dir / "scenario" / "scenario_1" / "attempt_1.stdout.log"
    assert scenario_stdout.exists()

    assert scenario_stdout.read_text(encoding="utf-8") == "Hello World\n"

    scenario_stdout = run_dir / "scenario" / "scenario_2" / "attempt_1.stdout.log"
    assert scenario_stdout.exists()

    assert scenario_stdout.read_text(encoding="utf-8") == ""

    report = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))

    assert report["metadata"]["runner_version"] == "1.5.1"

    assert report["summary"]["status"] == "FAILED"

    assert len(report["step_results"]) == 6


def test_integration_steps_succeeds_after_party(tmp_path: Path):
    output_dir = tmp_path / "artifacts"
    config_file = tmp_path / "config.yaml"

    config_file.write_text(
        f"""
        test_case:
          id: retry_integration
          name: retry integration
          description: subprocess retry
        device:
          serial: fake_serial
          product: fake_product
          build: fake_build
        retry:
          max_attempts: 3
          delay_seconds: 1
        lifecycle:
          global_setup:
            steps: []
          setup:
            steps: []
          scenario:
            steps:
              - name: unstable_command
                type: command
                command: |
                  COUNT_FILE=retry_count.txt
                  if [ ! -f \"$COUNT_FILE\" ]; then
                    echo 0 > \"$COUNT_FILE\"
                  fi

                  COUNT=$(cat \"$COUNT_FILE\")
                  COUNT=$((COUNT + 1))

                  echo \"$COUNT\" > \"$COUNT_FILE\"
                  echo \"attempt $COUNT\"

                  if [ \"$COUNT\" -lt 3 ]; then
                    echo \"temporary failure\" >&2
                    exit 1
                  fi

                  echo \"success\"
                  exit 0
                timeout_second: 5
          teardown:
            steps: []
          global_teardown:
            steps: []
        artifact:
          output_dir: "{output_dir}"
        """,
        encoding="utf-8",
    )

    config = ConfigLoader().load(str(config_file))
    runner = DeviceTestRunner(
        executor=SubprocessExecutor(project_directory=PROJECT_ROOT),
        artifact_manager=ArtifactManager(output_dir=str(output_dir)),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    assert result.summary.status == "PASSED"

    step_result = result.step_results[0]

    assert step_result.attempts == 3
    assert step_result.attempt_results[0].success is False
    assert step_result.attempt_results[1].success is False
    assert step_result.attempt_results[2].success is True


def test_real_subprocess_fails_after_retry_exhausted(tmp_path: Path):
    output_dir = tmp_path / "artifacts"
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
        test_case:
          id: retry_integration
          name: retry integration
          description: subprocess retry
        device:
          serial: fake_serial
          product: fake_product
          build: fake_build
        retry:
          max_attempts: 3
          delay_seconds: 1
        lifecycle:
          global_setup:
            steps: []
          setup:
            steps: []
          scenario:
            steps:
              - name: unstable_command
                type: command
                command: |
                  echo "always fail" >&2
                  exit 1
                timeout_second: 5
          teardown:
            steps: []
          global_teardown:
            steps: []
        artifact:
          output_dir: "{output_dir}"
        """,
        encoding="utf-8",
    )

    config = ConfigLoader().load(str(config_file))
    runner = DeviceTestRunner(
        executor=SubprocessExecutor(project_directory=PROJECT_ROOT),
        artifact_manager=ArtifactManager(output_dir=str(output_dir)),
        artifact_validator=ArtifactValidator(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    assert result.summary.status == "FAILED"
    assert result.step_results[0].attempts == 3
