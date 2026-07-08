from runner.executor import SubprocessScenarioExecutor
from runner.models import TestConfig, TestResult
from runner.reporter import JsonReporter


class DeviceTestRunner:
    def __init__(
        self,
        executor: SubprocessScenarioExecutor,
        reporter: JsonReporter,
    ):
        self.executor = executor
        self.reporter = reporter

    def run(self, config: TestConfig) -> TestResult:
        result = self.executor.run(test_name=config.test_name, scenario=config.scenario)

        self.reporter.save(result=result, output_dir=config.artifact.output_dir)
        return result
