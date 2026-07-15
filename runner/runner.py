import time

from runner.artifact import ArtifactManager
from runner.executor import SubprocessExecutor
from runner.models import ExecutionSummary, RunMetadata, RunnerConfig, RunResult
from runner.reporter import JsonReporter


class DeviceTestRunner:
    def __init__(
        self,
        executor: SubprocessExecutor,
        reporter: JsonReporter,
    ):
        self.executor = executor
        self.reporter = reporter

    def run(self, config: RunnerConfig) -> RunResult:
        artifact_manager = ArtifactManager(output_dir=config.artifact.output_dir)

        run_dir = artifact_manager.create_run_directory(test_case_id=config.test_case.id)

        step_results = []

        status = "PASSED"

        passed_steps = 0

        start_time = time.time()

        for step in config.workflow.steps:
            result = self.executor.execute(step=step)
            step_results.append(result)

            artifact_manager.save_stdout(run_dir=run_dir, step_name=step.name, stdout=result.stdout)

            artifact_manager.save_stderr(run_dir=run_dir, step_name=step.name, stderr=result.stderr)

            if result.success:
                passed_steps += 1

            else:
                status = "FAILED"
                break

        duration = time.time() - start_time

        metadata = RunMetadata(
            test_case_id=config.test_case.id,
            test_case_name=config.test_case.name,
            device_serial=config.device.serial,
            device_product=config.device.product,
            device_build=config.device.build,
            runner_version="1.2",
        )

        summary = ExecutionSummary(
            status=status,
            total_steps=len(config.workflow.steps),
            passed_steps=passed_steps,
            failed_steps=len(config.workflow.steps) - passed_steps,
            duration_seconds=duration,
        )

        run_result = RunResult(
            metadata=metadata,
            summary=summary,
            artifact_dir=str(run_dir),
            step_results=step_results,
        )

        self.reporter.save(result=run_result, output_dir=str(run_dir))

        return run_result
