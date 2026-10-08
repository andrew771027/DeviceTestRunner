# Device Test Runner v1.6.3 Architecture

Version scope: Cancellation-Aware Cleanup. Source baseline: `f9337ec` plus the inspected working tree, compared with tag `v1.6.2`. This describes implementation, not a verified release.

## Purpose and components

Runner separates normal execution from cleanup. `ConfigLoader.load()` reads optional finite positive `run_timeout_seconds` and `cleanup_timeout_seconds`; missing/null values mean unlimited scope duration. Direct Python dataclass construction does not apply loader validation.

`DeviceTestRunner.run(config, cancellation_token=None)` creates the artifact directory, starts an optional run watchdog and executes global_setup, setup and scenario. It stops that watchdog in a finally block before starting cleanup. Global setup success determines whether teardown runs. Global teardown is attempted regardless of global setup success unless cleanup is already cancelled.

`CleanupScope.create(timeout_seconds)` creates a fresh token and optional CleanupTimeoutWatchdog. Teardown, global teardown and their retry delays share this token and deadline. Ordinary failure does not stop remaining cleanup steps. Scope cancellation prevents new work. Process termination and reader draining may extend past the deadline.

```mermaid
classDiagram
    class DeviceTestRunner {
        run(config, cancellation_token) RunResult
        _run_cleanup(config, run_dir, step_results, run_setup_completed) CleanupSummary
        _run_stage(stage, steps, config, run_dir, step_results, stop_on_failure, cancellation_token) bool
    }
    class RunnerConfig {
        run_timeout_seconds
        cleanup_timeout_seconds
    }
    class CancellationToken {
        cancel(reason)
        is_cancelled
        reason
    }
    class CancellationWatchdog {
        start()
        stop()
        deadline
    }
    class RunTimeoutWatchdog
    class CleanupTimeoutWatchdog
    class CleanupScope {
        create(timeout_seconds) CleanupScope
        start()
        stop()
    }
    class SubprocessExecutor {
        execute(step, stage, attempt, log_writer, working_directory, cancellation_token)
    }
    class ProcessTerminator {
        terminate_process_group(process)
    }
    class ArtifactValidator {
        validate_all(rules, base_dir)
    }
    class JsonReporter {
        save(result, output_dir)
    }
    class CleanupSummary {
        attempted
        timed_out
        failed
        cancellation_reason
    }
    class RunResult {
        metadata
        summary
        cleanup_summary
        step_results
        artifact_validation_results
    }
    CancellationWatchdog <|-- RunTimeoutWatchdog
    CancellationWatchdog <|-- CleanupTimeoutWatchdog
    CancellationWatchdog --> CancellationToken
    CleanupScope *-- CancellationToken
    CleanupScope o-- CleanupTimeoutWatchdog
    DeviceTestRunner --> RunnerConfig
    DeviceTestRunner --> RunTimeoutWatchdog
    DeviceTestRunner --> CleanupScope
    DeviceTestRunner --> SubprocessExecutor
    SubprocessExecutor --> ProcessTerminator
    DeviceTestRunner --> ArtifactValidator
    DeviceTestRunner --> JsonReporter
    RunResult *-- CleanupSummary
```

## Execution flow

```mermaid
sequenceDiagram
    participant Caller
    participant Runner as DeviceTestRunner
    participant RunWatchdog as RunTimeoutWatchdog
    participant Executor as SubprocessExecutor
    participant Cleanup as CleanupScope
    participant Validator as ArtifactValidator
    participant Reporter as JsonReporter
    Caller->>Runner: run(config, run_token)
    opt run_timeout_seconds configured
        Runner->>RunWatchdog: start()
    end
    opt run token active
        Runner->>Executor: global_setup(run_token)
        opt global_setup succeeded and run token active
            Runner->>Executor: setup(run_token)
            opt setup succeeded and run token active
                Runner->>Executor: scenario(run_token)
            end
        end
    end
    opt run watchdog exists
        Runner->>RunWatchdog: stop() in finally
    end
    Runner->>Cleanup: create(cleanup_timeout_seconds)
    Runner->>Cleanup: start()
    opt global_setup succeeded
        Runner->>Executor: teardown(cleanup_token), stop_on_failure=false
    end
    opt cleanup token active
        Runner->>Executor: global_teardown(cleanup_token), stop_on_failure=false
    end
    Runner->>Cleanup: stop() in finally
    Cleanup-->>Runner: token reason determines CleanupSummary
    Runner->>Validator: validate_all(all rules, run_dir)
    Validator-->>Runner: final artifact results
    Runner->>Runner: calculate_run_status and build RunResult
    Runner->>Reporter: save(result, run_dir)
    Runner-->>Caller: RunResult
```

A watchdog may cancel its token while an executor attempt or retry delay runs. Executor uses ProcessTerminator to stop the attempt group. Cancelled attempts skip validation and retry. Final validation still evaluates every configured rule after cleanup.

## Results and compatibility

`RunnerConfig.cleanup_timeout_seconds` is optional. `RunResult.cleanup_summary` is required for Python callers constructing results directly. JsonReporter serializes it with the rest of the dataclass. `attempted` means a cleanup stage route was entered, including an empty stage; it does not count launched processes. `timed_out` is true when the cleanup token reason is CLEANUP_TIMEOUT. `failed` includes ordinary cleanup failure and scope timeout.

Metadata keeps the original run reason, run timeout and `run_timed_out`; it does not include cleanup_timeout_seconds. Status priority is RUN_TIMEOUT → TIMED_OUT, USER_REQUEST → CANCELLED, cleanup failure → FAILED, cancelled steps → CANCELLED, failed/skipped steps → FAILED, required artifact failure → FAILED, otherwise PASSED.

The shared CancellationWatchdog supplies monotonic deadline and stop-event waiting for both scope watchdog subclasses. `ignore_cancellation` is not part of runner/executor interfaces; separate tokens provide the cleanup behavior.

## Limits

Unexpected exceptions in normal work stop the run watchdog but can bypass cleanup, validation and reporting. Cleanup exceptions stop its watchdog but can bypass reporting. A second SIGINT raises KeyboardInterrupt. Detached descendants and normally exiting parents with surviving background children retain the process limitations described in [Process Lifecycle](../process_lifecycle.md). TIMED_OUT still falls through to CLI exit code 0.

See [Cleanup guide](../cancellation_aware_cleanup.md), [test matrix](../test_matrix/test_matrix_v1.6.3.md) and [completion checklist](../definition_of_done/definition_of_done_v1.6.3.md).
