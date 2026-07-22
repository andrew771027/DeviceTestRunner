import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from runner.artifact import ArtifactManager
from runner.executor import SubprocessExecutor
from runner.models import (
    ExecutionSummary,
    LifecycleSteps,
    RunMetadata,
    RunnerConfig,
    RunResult,
    StepResult,
)
from runner.reporter import JsonReporter


class DeviceTestRunner:
    VERSION = "1.3"

    def __init__(
        self,
        executor: SubprocessExecutor,
        reporter: JsonReporter,
    ):
        self.executor = executor
        self.reporter = reporter

    def run(self, config: RunnerConfig) -> RunResult:
        started_at = datetime.now(timezone.utc)
        started_counter = time.perf_counter()

        artifact_manager = ArtifactManager(output_dir=config.artifact.output_dir)

        run_dir = artifact_manager.create_run_directory(test_case_id=config.test_case.id)

        step_results: list[StepResult] = []

        global_setup_success = self._run_stage(
            stage="global_setup",
            steps=config.lifecycle.global_setup.steps,
            run_dir=run_dir,
            artifact_manager=artifact_manager,
            step_results=step_results,
            stop_on_failure=True,
        )

        if global_setup_success:

            setup_success = self._run_stage(
                stage="setup",
                steps=config.lifecycle.setup.steps,
                run_dir=run_dir,
                artifact_manager=artifact_manager,
                step_results=step_results,
                stop_on_failure=True,
            )

            if setup_success:

                self._run_stage(
                    stage="scenario",
                    steps=config.lifecycle.scenario.steps,
                    run_dir=run_dir,
                    artifact_manager=artifact_manager,
                    step_results=step_results,
                    stop_on_failure=True,
                )

                self._run_stage(
                    stage="teardown",
                    steps=config.lifecycle.teardown.steps,
                    run_dir=run_dir,
                    artifact_manager=artifact_manager,
                    step_results=step_results,
                    stop_on_failure=False,
                )

            self._run_stage(
                stage="global_teardown",
                steps=config.lifecycle.global_teardown.steps,
                run_dir=run_dir,
                artifact_manager=artifact_manager,
                step_results=step_results,
                stop_on_failure=False,
            )

        finished_at = datetime.now(timezone.utc)

        duration_deconds = time.perf_counter() - started_counter

        run_result = self._build_run_result(
            config=config,
            run_dir=run_dir,
            step_results=step_results,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_deconds,
        )

        self.reporter.save(result=run_result, output_dir=str(run_dir))

        return run_result

    def _run_stage(
        self,
        stage: str,
        steps: List[LifecycleSteps],
        run_dir: Path,
        artifact_manager: ArtifactManager,
        step_results: List[StepResult],
        stop_on_failure: bool,
    ) -> bool:

        stage_success = True

        for step in steps:
            result = self.executor.execute(step, stage)
            step_results.append(result)

            artifact_manager.save_step_stdout(
                run_dir=run_dir,
                stage=stage,
                step_name=result.name,
                stdout=result.stdout,
            )

            artifact_manager.save_step_stderr(
                run_dir=run_dir,
                stage=stage,
                step_name=result.name,
                stderr=result.stderr,
            )

            if not result.success:
                stage_success = False

                if stop_on_failure:
                    break

        return stage_success

    def _build_run_result(
        self,
        config: RunnerConfig,
        run_dir: Path,
        step_results: List[StepResult],
        started_at: datetime,
        finished_at: datetime,
        duration_seconds: float,
    ) -> RunResult:

        configured_steps = self._count_configured_steps(config)

        executed_steps = len(step_results)

        passed_steps = sum(1 for result in step_results if result.success)

        failed_steps = sum(1 for result in step_results if not result.success)

        skipped_steps = configured_steps - executed_steps

        status = "PASSED" if failed_steps == 0 and skipped_steps == 0 else "FAILED"

        metadata = RunMetadata(
            test_case_id=config.test_case.id,
            test_case_name=config.test_case.name,
            test_case_description=config.test_case.description,
            device_serial=config.device.serial,
            device_product=config.device.product,
            device_build=config.device.build,
            runner_version=self.VERSION,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
        )

        summary = ExecutionSummary(
            status=status,
            configured_steps=configured_steps,
            executed_steps=executed_steps,
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            duration_seconds=duration_seconds,
        )

        run_reuslt = RunResult(
            metadata=metadata,
            summary=summary,
            step_results=step_results,
            artifact_dir=str(run_dir),
        )

        return run_reuslt

    @staticmethod
    def _count_configured_steps(config: RunnerConfig) -> int:
        lifecycle = config.lifecycle

        return sum(
            len(steps)
            for steps in (
                lifecycle.global_setup.steps,
                lifecycle.setup.steps,
                lifecycle.scenario.steps,
                lifecycle.teardown.steps,
                lifecycle.global_teardown.steps,
            )
        )
