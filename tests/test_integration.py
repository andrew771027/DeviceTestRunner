from runner.config import ConfigLoader
from runner.executor import SubprocessScenarioExecutor
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner


def test_integration_loader_runner_executor(tmp_path):
    config_file = tmp_path / "intergration.yaml"
    config_file.write_text(
        """
test_name: intergration_test

scenario:
  command: "echo intergration_test"
  timeout_second: 1

artifact:
  output_dir: "runs/intergration_test"
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(str(config_file))
    runner = DeviceTestRunner(executor=SubprocessScenarioExecutor(), reporter=JsonReporter())
    result = runner.executor.run(test_name=config.test_name, scenario=config.scenario)

    assert result.test_name == "intergration_test"
    assert result.success is True
    assert "intergration_test" in result.stdout
