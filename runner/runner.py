from runner.executor import CommandStepExecutor
from runner.models import RunnerConfig, RunResult
from runner.reporter import JsonReporter


class DeviceTestRunner:
    def __init__(
        self,
        executor: CommandStepExecutor,
        reporter: JsonReporter,
    ):
        self.executor = executor
        self.reporter = reporter

    def run(self, config: RunnerConfig) -> RunResult:
        step_results = []

        for step in config.workflow.steps:
            result = self.executor.execute(step=step)
            step_results.append(result)

            if not result.success:
                break

        run_success = all(result.success for result in step_results)

        run_result = RunResult(
            test_case_id=config.test_case.id,
            test_case_name=config.test_case.name,
            success=run_success,
            step_results=step_results,
        )

        self.reporter.save(result=run_result, output_dir=config.artifact.output_dir)
        return run_result
