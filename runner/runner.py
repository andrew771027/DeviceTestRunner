import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from runner.artifact import ArtifactManager
from runner.artifact_validator import ArtifactValidator
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.models import (
    ArtifactValidationResult,
    ArtifactValidationRule,
    ExecutionSummary,
    FailureType,
    LifecycleSteps,
    RunMetadata,
    RunnerConfig,
    RunResult,
    StepAttemptResult,
    StepResult,
)
from runner.reporter import JsonReporter
from runner.retry import RetryPolicy


class DeviceTestRunner:
    VERSION = "1.5.2"

    def __init__(
        self,
        executor: SubprocessExecutor,
        artifact_manager: ArtifactManager,
        artifact_validator: ArtifactValidator,
        failure_classifier: FailureClassifier,
        reporter: JsonReporter,
        show_console_output: bool = True,
    ):
        self.executor = executor
        self.artifact_manager = artifact_manager
        self.artifact_validator = artifact_validator
        self.failure_classifier = failure_classifier
        self.reporter = reporter

        self.show_console_output = show_console_output

    def run(self, config: RunnerConfig) -> RunResult:
        started_at = datetime.now(timezone.utc)
        started_counter = time.perf_counter()
        artifact_results: List[ArtifactValidationResult] = []

        run_dir = self.artifact_manager.create_run_directory(test_case_id=config.test_case.id)

        step_results: list[StepResult] = []

        global_setup_success = self._run_stage(
            stage="global_setup",
            steps=config.lifecycle.global_setup.steps,
            config=config,
            run_dir=run_dir,
            artifact_manager=self.artifact_manager,
            step_results=step_results,
            stop_on_failure=True,
        )

        if global_setup_success:

            setup_success = self._run_stage(
                stage="setup",
                steps=config.lifecycle.setup.steps,
                config=config,
                run_dir=run_dir,
                artifact_manager=self.artifact_manager,
                step_results=step_results,
                stop_on_failure=True,
            )

            if setup_success:

                self._run_stage(
                    stage="scenario",
                    steps=config.lifecycle.scenario.steps,
                    config=config,
                    run_dir=run_dir,
                    artifact_manager=self.artifact_manager,
                    step_results=step_results,
                    stop_on_failure=True,
                )

                self._run_stage(
                    stage="teardown",
                    steps=config.lifecycle.teardown.steps,
                    config=config,
                    run_dir=run_dir,
                    artifact_manager=self.artifact_manager,
                    step_results=step_results,
                    stop_on_failure=False,
                )

        self._run_stage(
            stage="global_teardown",
            steps=config.lifecycle.global_teardown.steps,
            config=config,
            run_dir=run_dir,
            artifact_manager=self.artifact_manager,
            step_results=step_results,
            stop_on_failure=False,
        )

        # 最終 Run-level Artifact Validation
        artifact_results = self.artifact_validator.validate_all(
            rules=config.artifact.validation.rules, base_dir=run_dir
        )

        finished_at = datetime.now(timezone.utc)

        duration_deconds = time.perf_counter() - started_counter

        run_result = self._build_run_result(
            config=config,
            run_dir=run_dir,
            step_results=step_results,
            artifact_results=artifact_results,
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
        config: RunnerConfig,
        run_dir: Path,
        artifact_manager: ArtifactManager,
        step_results: List[StepResult],
        stop_on_failure: bool,
    ) -> bool:

        stage_success = True
        retry_policy = RetryPolicy(config=config.retry)

        for step in steps:

            attempt_results: list[StepAttemptResult] = []

            step_started_at = time.perf_counter()

            step_success = False

            retry_rules = self._get_retry_rules_for_step(step_name=step.name, config=config)

            for attempt in range(1, config.retry.max_attempts + 1):

                log_writer = artifact_manager.create_step_log_writer(
                    run_dir=run_dir,
                    stage=stage,
                    step_name=step.name,
                    attempt=attempt,
                    show_console=self.show_console_output,
                )

                with log_writer:
                    process_result = self.executor.execute(
                        step=step,
                        stage=stage,
                        attempt=attempt,
                        log_writer=log_writer,
                        working_directory=run_dir,
                    )

                artifact_results: list[ArtifactValidationResult] = []

                # 只有 process 成功時，
                # artifact validation 才有意義。
                if process_result.success and retry_rules:
                    artifact_results = self.artifact_validator.validate_all(
                        rules=retry_rules, base_dir=run_dir
                    )

                artifact_failure_type = self.failure_classifier.classify_artifact_failure(
                    artifact_results=artifact_results
                )

                #
                # Failure priority:
                #
                # Process Failure
                #     >
                # Artifact Failure
                #     >
                # NONE
                #
                if not process_result.success:
                    final_failure_type = process_result.failure_type
                elif artifact_failure_type != FailureType.NONE:
                    final_failure_type = artifact_failure_type
                else:
                    final_failure_type = FailureType.NONE

                attempt_success = final_failure_type == FailureType.NONE

                # attempt_success = process_result.success and all(
                # result.passed for result in artifact_results
                # )

                attempt_result = StepAttemptResult(
                    attempt=attempt,
                    success=attempt_success,
                    failure_type=(final_failure_type),
                    exit_code=process_result.exit_code,
                    duration_seconds=process_result.duration_seconds,
                    stdout=process_result.stdout,
                    stderr=process_result.stderr,
                    stdout_log_path=process_result.stdout_log_path,
                    stderr_log_path=process_result.stderr_log_path,
                    error=process_result.error,
                    artifact_validation_results=artifact_results,
                )

                attempt_results.append(attempt_result)

                if attempt_success:
                    step_success = True
                    break

                should_retry = retry_policy.should_retry(
                    attempt=attempt,
                    failure_type=(final_failure_type),
                )

                if not should_retry:
                    break

                if retry_policy.delay_seconds > 0:
                    time.sleep(retry_policy.delay_seconds)

            step_duration_seconds = time.perf_counter() - step_started_at

            step_result = StepResult(
                stage=stage,
                name=step.name,
                command=step.command,
                success=step_success,
                attempts=len(attempt_results),
                attempt_results=attempt_results,
                duration_seconds=step_duration_seconds,
            )

            step_results.append(step_result)

            if not step_result.success:
                stage_success = False

                if stop_on_failure:
                    break

        return stage_success

    def _build_run_result(
        self,
        config: RunnerConfig,
        run_dir: Path,
        step_results: List[StepResult],
        artifact_results: list[ArtifactValidationResult],
        started_at: datetime,
        finished_at: datetime,
        duration_seconds: float,
    ) -> RunResult:

        configured_steps = self._count_configured_steps(config)

        executed_steps = len(step_results)

        passed_steps = sum(1 for result in step_results if result.success)

        failed_steps = sum(1 for result in step_results if not result.success)

        skipped_steps = configured_steps - executed_steps

        configured_artifact_rules = len(artifact_results)

        passed_artifact_rules = sum(result.passed for result in artifact_results)

        failed_artifact_rules = sum(not result.passed for result in artifact_results)

        status = self._calculate_status(
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            failed_artifact_rules=failed_artifact_rules,
        )

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
            configured_artifact_rules=(configured_artifact_rules),
            passed_artifact_rules=(passed_artifact_rules),
            failed_artifact_rules=(failed_artifact_rules),
            duration_seconds=duration_seconds,
        )

        run_reuslt = RunResult(
            metadata=metadata,
            summary=summary,
            step_results=step_results,
            artifact_validation_results=(artifact_results),
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

    @staticmethod
    def _calculate_status(failed_steps: int, skipped_steps: int, failed_artifact_rules: int) -> str:
        if failed_steps > 0:
            return "FAILED"

        if skipped_steps > 0:
            return "FAILED"

        if failed_artifact_rules > 0:
            return "FAILED"

        return "PASSED"

    @staticmethod
    def _get_retry_rules_for_step(
        step_name: str,
        config: RunnerConfig,
    ) -> list[ArtifactValidationRule]:

        return [
            rule
            for rule in config.artifact.validation.rules
            if rule.after_step == step_name and rule.retry_on_failure is True
        ]
