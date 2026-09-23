import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from runner.artifact import ArtifactManager
from runner.artifact_validator import ArtifactValidator
from runner.cancellation import CancellationReason, CancellationToken
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.models import (
    ArtifactValidationResult,
    ArtifactValidationRule,
    ExecutionSummary,
    FailureType,
    LifecycleStepContent,
    LifecycleSteps,
    RunMetadata,
    RunnerConfig,
    RunResult,
    StepAttemptResult,
    StepResult,
)
from runner.reporter import JsonReporter
from runner.retry import RetryPolicy
from runner.run_status import calculate_run_status
from runner.run_timeout import RunTimeoutWatchdog


class DeviceTestRunner:
    VERSION = "1.6.2"

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

    def run(
        self, config: RunnerConfig, cancellation_token: CancellationToken | None = None
    ) -> RunResult:

        if cancellation_token is None:
            cancellation_token = CancellationToken()

        started_at = datetime.now(timezone.utc)

        started_counter = time.perf_counter()

        artifact_results: List[ArtifactValidationResult] = []

        run_dir = self.artifact_manager.create_run_directory(test_case_id=config.test_case.id)

        step_results: List[StepResult] = []

        global_setup_success = False

        setup_success = False

        watchdog: RunTimeoutWatchdog | None = None

        if config.run_timeout_seconds is not None:

            watchdog = RunTimeoutWatchdog(
                timeout_seconds=config.run_timeout_seconds,
                cancellation_token=cancellation_token,
            )

            watchdog.start()

        try:

            #
            # NORMAL LIFECYCLE
            #
            if not cancellation_token.is_cancelled:

                global_setup_success = self._run_stage(
                    stage="global_setup",
                    steps=config.lifecycle.global_setup.steps,
                    config=config,
                    run_dir=run_dir,
                    step_results=step_results,
                    stop_on_failure=True,
                    cancellation_token=cancellation_token,
                    ignore_cancellation=False,
                )

            if global_setup_success and not cancellation_token.is_cancelled:

                setup_success = self._run_stage(
                    stage="setup",
                    steps=config.lifecycle.setup.steps,
                    config=config,
                    run_dir=run_dir,
                    step_results=step_results,
                    stop_on_failure=True,
                    cancellation_token=cancellation_token,
                    ignore_cancellation=False,
                )

                if setup_success and not cancellation_token.is_cancelled:

                    self._run_stage(
                        stage="scenario",
                        steps=config.lifecycle.scenario.steps,
                        config=config,
                        run_dir=run_dir,
                        step_results=step_results,
                        stop_on_failure=True,
                        cancellation_token=cancellation_token,
                        ignore_cancellation=False,
                    )

            #
            # teardown 是 cleanup lifecycle。
            #
            # 即使 cancellation token 已經是 cancelled，
            # teardown 還是要執行。
            #
            if global_setup_success:

                self._run_stage(
                    stage="teardown",
                    steps=config.lifecycle.teardown.steps,
                    config=config,
                    run_dir=run_dir,
                    step_results=step_results,
                    stop_on_failure=False,
                    cancellation_token=cancellation_token,
                    ignore_cancellation=True,
                )

            #
            # global teardown 永遠 best effort。
            #
            self._run_stage(
                stage="global_teardown",
                steps=config.lifecycle.global_teardown.steps,
                config=config,
                run_dir=run_dir,
                step_results=step_results,
                stop_on_failure=False,
                cancellation_token=cancellation_token,
                ignore_cancellation=True,
            )

            #
            # FINAL ARTIFACT VALIDATION
            #
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
                cancellation_token=cancellation_token,
            )

            self.reporter.save(result=run_result, output_dir=str(run_dir))

            return run_result

        finally:

            if watchdog is not None:
                watchdog.stop()

    def _run_stage(
        self,
        stage: str,
        steps: List[LifecycleSteps],
        config: RunnerConfig,
        run_dir: Path,
        step_results: List[StepResult],
        stop_on_failure: bool,
        cancellation_token: CancellationToken,
        ignore_cancellation: bool,
    ) -> bool:

        stage_success = True
        retry_policy = RetryPolicy(config=config.retry)

        for step in steps:

            if cancellation_token.is_cancelled and not ignore_cancellation:
                return False

            step_result = self._run_step_with_retry(
                stage=stage,
                step=step,
                config=config,
                retry_policy=retry_policy,
                run_dir=run_dir,
                cancellation_token=cancellation_token,
                ignore_cancellation=ignore_cancellation,
            )

            step_results.append(step_result)

            if step_result.cancelled:
                stage_success = False
                break

            if not step_result.success:
                stage_success = False

                if stop_on_failure:
                    break

        return stage_success

    def _run_step_with_retry(
        self,
        stage: str,
        step: LifecycleStepContent,
        config: RunnerConfig,
        retry_policy: RetryPolicy,
        run_dir: Path,
        cancellation_token: CancellationToken,
        ignore_cancellation: bool,
    ) -> StepResult:

        attempt_results: List[StepAttemptResult] = []

        #
        # 找出這個 step 跑完後需要驗證的 Artifact Rules。
        #
        artifact_rules = self._get_rules_for_step(step_name=step.name, config=config)

        step_started_at = time.perf_counter()

        step_success = False

        step_cancelled = False

        #
        # 一個 Step 最多執行 max_attempts 次。
        #
        for attempt in range(1, config.retry.max_attempts + 1):

            #
            # ---------------------------------------------------------
            # 1. Attempt 開始前先檢查 Cancellation
            # ---------------------------------------------------------
            #
            # Normal lifecycle:
            #
            #   cancel → 不要再啟動新的 attempt
            #
            # Cleanup lifecycle:
            #
            #   teardown/global_teardown
            #   可以 ignore cancellation
            #
            if cancellation_token.is_cancelled and not ignore_cancellation:
                step_cancelled = True
                break

            #
            # Cleanup stage 不應該使用已經 cancelled 的 token。
            #
            # 不然 teardown 一開始：
            #
            # cancellation_token.is_cancelled == True
            #
            # Executor 又會立刻把 cleanup process cancel。
            #
            execution_token = CancellationToken() if ignore_cancellation else cancellation_token

            #
            # ---------------------------------------------------------
            # 2. 為這一次 Attempt 建立獨立 log
            # ---------------------------------------------------------
            #
            log_writer = self.artifact_manager.create_step_log_writer(
                run_dir=run_dir,
                stage=stage,
                step_name=step.name,
                attempt=attempt,
                show_console=self.show_console_output,
            )

            #
            # ---------------------------------------------------------
            # 3. 執行 Process
            # ---------------------------------------------------------
            #
            # Executor 的責任：
            #
            # - start subprocess
            # - stdout/stderr streaming
            # - timeout
            # - cancellation
            # - terminate process tree
            # - wait until process cleanup finished
            #
            # Runner 不直接碰 PID / process group。
            #
            with log_writer:
                process_result = self.executor.execute(
                    step=step,
                    stage=stage,
                    attempt=attempt,
                    log_writer=log_writer,
                    working_directory=run_dir,
                    cancellation_token=execution_token,
                )

            artifact_results: List[ArtifactValidationResult] = []
            #
            # ---------------------------------------------------------
            # 4. 如果 Process 被 Cancel
            # ---------------------------------------------------------
            #
            # Cancelled:
            #
            # - 不做 artifact validation
            # - 不 retry
            # - Step = CANCELLED
            #
            if process_result.cancelled:
                attempt_results.append(process_result)
                step_cancelled = True
                break

            #
            # ---------------------------------------------------------
            # 5. Process PASS 才做 Attempt-level Artifact Validation
            # ---------------------------------------------------------
            #

            # 只有 process 成功時，
            # artifact validation 才有意義。
            if process_result.success and artifact_rules:
                artifact_results = self.artifact_validator.validate_all(
                    rules=artifact_rules, base_dir=run_dir
                )

            #
            # ---------------------------------------------------------
            # 6. 只讓 required Artifact 影響 Attempt Success
            # ---------------------------------------------------------
            #
            # optional artifact:
            #
            # validation FAIL
            # → report 留著
            # → 但不影響 step success
            #
            required_artifact_results = self._get_required_artifact_results(artifact_results)

            #
            # ---------------------------------------------------------
            # 7. Artifact Failure Classification
            # ---------------------------------------------------------
            #
            artifact_failure_type = self.failure_classifier.classify_artifact_failure(
                artifact_results=required_artifact_results
            )

            #
            # ---------------------------------------------------------
            # 8. 決定這次 Attempt 的最終 FailureType
            # ---------------------------------------------------------
            #
            # Priority:
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

            #
            # ---------------------------------------------------------
            # 9. Attempt Success
            # ---------------------------------------------------------
            #
            attempt_success = final_failure_type == FailureType.NONE

            #
            # ---------------------------------------------------------
            # 10. 建立完整 Attempt Result
            # ---------------------------------------------------------
            #
            attempt_result = StepAttemptResult(
                attempt=attempt,
                success=attempt_success,
                timed_out=process_result.timed_out,
                cancelled=False,
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

            #
            # ---------------------------------------------------------
            # 11. PASS → Step 完成
            # ---------------------------------------------------------
            #
            if attempt_success:
                step_success = True
                break

            #
            # ---------------------------------------------------------
            # 12. 再次檢查 Cancellation
            # ---------------------------------------------------------
            #
            # 有可能 process 剛結束，
            # 但使用者這時候按下 cancel。
            #

            if cancellation_token.is_cancelled and not ignore_cancellation:
                step_cancelled = True
                break

            #
            # ---------------------------------------------------------
            # 13. Retry Policy
            # ---------------------------------------------------------
            #
            should_retry = retry_policy.should_retry(
                attempt=attempt,
                failure_type=(final_failure_type),
            )

            if not should_retry:
                break

            #
            # ---------------------------------------------------------
            # 14. Retry 前 Cleanup Artifact
            # ---------------------------------------------------------
            #
            # 這一步是為了避免：
            #
            # Attempt 1:
            #   power.csv 產生
            #   validation fail
            #
            # Attempt 2:
            #   沒重新產生
            #
            # Validator 卻讀到 Attempt 1 的 stale file。
            #
            required_rules = [rule for rule in artifact_rules if rule.required]

            if required_rules:
                self.artifact_manager.cleanup_validation_targets(
                    run_dir=run_dir, rules=required_rules
                )

            #
            # ---------------------------------------------------------
            # 15. Retry Delay
            # ---------------------------------------------------------
            #
            # 不直接 time.sleep(delay_seconds)
            #
            # 因為 sleep 期間也要能被 cancel。
            #
            if retry_policy.delay_seconds > 0:
                cancelled_during_delay = self._wait_retry_delay(
                    delay_seconds=retry_policy.delay_seconds,
                    cancellation_token=cancellation_token,
                )

                if cancelled_during_delay and not ignore_cancellation:
                    step_cancelled = True
                    break

            #
            # loop 回到下一個 attempt
            #

        #
        # -------------------------------------------------------------
        # 16. Step Result
        # -------------------------------------------------------------
        #
        duration_seconds = time.perf_counter() - step_started_at

        return StepResult(
            stage=stage,
            name=step.name,
            command=step.command,
            success=step_success,
            cancelled=step_cancelled,
            attempts=len(attempt_results),
            attempt_results=attempt_results,
            duration_seconds=duration_seconds,
        )

    def _wait_retry_delay(
        self, delay_seconds: float, cancellation_token: CancellationToken
    ) -> bool:

        deadline = time.monotonic() + delay_seconds

        while True:

            if cancellation_token.is_cancelled:
                return True

            remaining = deadline - time.monotonic()

            if remaining <= 0:
                return False

            time.sleep(min(0.1, remaining))

    def _build_run_result(
        self,
        config: RunnerConfig,
        run_dir: Path,
        step_results: List[StepResult],
        artifact_results: List[ArtifactValidationResult],
        started_at: datetime,
        finished_at: datetime,
        duration_seconds: float,
        cancellation_token: CancellationToken,
    ) -> RunResult:

        configured_steps = self._count_configured_steps(config)

        executed_steps = len(step_results)

        passed_steps = sum(1 for result in step_results if result.success)

        cancelled_steps = sum(1 for result in step_results if result.cancelled)

        failed_steps = sum(
            1 for result in step_results if not result.success and not result.cancelled
        )

        skipped_steps = configured_steps - executed_steps

        configured_artifact_rules = len(artifact_results)

        passed_artifact_rules = sum(1 for result in artifact_results if result.passed)

        failed_artifact_rules = sum(1 for result in artifact_results if not result.passed)

        failed_required_artifact_rules = sum(
            1 for result in artifact_results if (result.required and not result.passed)
        )

        status = calculate_run_status(
            cancellation_reason=cancellation_token.reason,
            failed_steps=failed_steps,
            cancelled_steps=cancelled_steps,
            skipped_steps=skipped_steps,
            failed_required_artifact_rules=failed_required_artifact_rules,
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
            cancel_requested=cancellation_token.is_cancelled,
            cancel_reason=(
                cancellation_token.reason.value if cancellation_token.reason is not None else None
            ),
            run_timeout_seconds=config.run_timeout_seconds,
            run_timed_out=(cancellation_token.reason == CancellationReason.RUN_TIMEOUT),
        )

        summary = ExecutionSummary(
            status=status,
            configured_steps=configured_steps,
            executed_steps=executed_steps,
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            cancelled_steps=cancelled_steps,
            skipped_steps=skipped_steps,
            configured_artifact_rules=(configured_artifact_rules),
            passed_artifact_rules=(passed_artifact_rules),
            failed_artifact_rules=(failed_artifact_rules),
            failed_required_artifact_rules=(failed_required_artifact_rules),
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
    def _get_rules_for_step(
        step_name: str,
        config: RunnerConfig,
    ) -> List[ArtifactValidationRule]:

        return [rule for rule in config.artifact.validation.rules if rule.after_step == step_name]

    @staticmethod
    def _get_required_artifact_results(
        artifact_results: List[ArtifactValidationResult],
    ) -> List[ArtifactValidationResult]:

        return [result for result in artifact_results if result.required]
