from runner.config import ConfigLoader
from runner.executor import SubprocessExecutor
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner


def test_integration_loader_runner_executor_success(tmp_path):
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

workflow:
  steps:
    - name: step_1
      type: command
      command: "echo 'Hello World1'"
      timeout_second: 10
    - name: step_2
      type: command
      command: "echo 'Hello World2'"
      timeout_second: 5
    - name: step_3
      type: command
      command: "echo 'Hello World3'"
      timeout_second: 1

artifact:
  output_dir: "artifact/intergration_test"
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(str(config_file))
    runner = DeviceTestRunner(executor=SubprocessExecutor(), reporter=JsonReporter())
    result = runner.run(config)

    assert result.metadata.test_case_name == "intergration_test"
    assert result.passed is True

    assert len(result.step_results) == 3

    assert result.step_results[0].step_name == "step_1"
    assert "Hello World1" in result.step_results[0].stdout

    assert result.step_results[1].step_name == "step_2"
    assert "Hello World2" in result.step_results[1].stdout

    assert result.step_results[2].step_name == "step_3"
    assert "Hello World3" in result.step_results[2].stdout

    assert "intergration_test" in result.metadata.test_case_name


def test_integration_stops_after_failed_command(tmp_path):

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

workflow:
  steps:
    - name: step_1
      type: command
      command: "echo 'Hello World1'"
      timeout_second: 10
    - name: step_2
      type: command
      command: "python -c 'import sys; sys.exit(1)'"
      timeout_second: 5
    - name: step_3
      type: command
      command: "echo 'Hello World3'"
      timeout_second: 1

artifact:
  output_dir: "artifact/intergration_test"
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_file)

    runner = DeviceTestRunner(executor=SubprocessExecutor(), reporter=JsonReporter())

    result = runner.run(config)

    assert len(result.step_results) == 2

    assert result.metadata.test_case_name == "intergration_test"
    assert result.passed is False

    assert len(result.step_results) == 2

    assert result.step_results[0].step_name == "step_1"
    assert "Hello World1" in result.step_results[0].stdout

    assert result.step_results[1].step_name == "step_2"
    assert result.step_results[1].stdout == ""

    assert "intergration_test" in result.metadata.test_case_name
