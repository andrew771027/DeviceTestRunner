import json
import shlex
import sys
from pathlib import Path

from runner.artifact import ArtifactManager
from runner.artifact_validator import ArtifactValidator
from runner.cancellation import CancellationReason, CancellationToken
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.models import (
    ArtifactConfig,
    DeviceInfo,
    DeviceTestCase,
    FailureType,
    LifecycleConfig,
    LifecycleStepContent,
    LifecycleSteps,
    RetryConfig,
    RunnerConfig,
)
from runner.process import ProcessTerminator
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner


def test_run_timout_stops_retry_and_runs_cleanup(tmp_path: Path):
    """Acceptance scenario.

    Given a long-running scenario has retries and a cleanup step.
    When the run deadline cancels the running process.
    Then cleanup runs and the report preserves one cancelled attempt with TIMED_OUT status.
    """

    project_root = Path(__file__).resolve().parents[2]

    fixture_script = project_root / "tests" / "fixtures" / "long_running.py"

    assert fixture_script.exists()

    marker = tmp_path / "cleanup.txt"

    python = shlex.quote(sys.executable)

    fixture = shlex.quote(str(fixture_script))

    marker_path = repr(str(marker))

    cleanup_command = f"{python} -c " + shlex.quote(
        "from pathlib import Path; "
        f"Path({marker_path}).write_text("
        "'cleanup completed', "
        "encoding='utf-8')"
    )

    config = RunnerConfig(
        test_case=DeviceTestCase(
            id="run_timeout_001",
            name="run_timeout_001",
            description="Run-level timeout test",
        ),
        device=DeviceInfo(
            serial="device_001",
            product="pixel",
            build="build_001",
        ),
        run_timeout_seconds=0.3,
        retry=RetryConfig(
            max_attempts=3,
            delay_seconds=0.1,
            retry_on=[FailureType.TIMEOUT, FailureType.DEVICE_OFFLINE],
        ),
        lifecycle=LifecycleConfig(
            global_setup=LifecycleSteps(steps=[]),
            setup=LifecycleSteps(steps=[]),
            scenario=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="long_running",
                        type="command",
                        command=f"{python} {fixture}",
                        timeout_second=30,
                    ),
                    LifecycleStepContent(
                        name="should_not_run",
                        type="command",
                        command="echo unexpected",
                        timeout_second=10,
                    ),
                ]
            ),
            teardown=LifecycleSteps(steps=[]),
            global_teardown=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="cleanup",
                        type="command",
                        command=cleanup_command,
                        timeout_second=10,
                    )
                ]
            ),
        ),
        artifact=ArtifactConfig(output_dir=str(tmp_path)),
    )

    classifier = FailureClassifier()

    runner = DeviceTestRunner(
        executor=SubprocessExecutor(
            project_directory=project_root,
            failure_classifier=classifier,
            process_terminator=ProcessTerminator(grace_period_seconds=0.2),
        ),
        artifact_manager=ArtifactManager(tmp_path),
        artifact_validator=ArtifactValidator(),
        failure_classifier=classifier,
        reporter=JsonReporter(),
        show_console_output=False,
    )

    token = CancellationToken()

    result = runner.run(config=config, cancellation_token=token)

    scenario_result = next(
        step_result for step_result in result.step_results if step_result.name == "long_running"
    )

    assert scenario_result.attempts == 1
    assert scenario_result.cancelled is True
    assert scenario_result.attempt_results[0].failure_type == FailureType.CANCELLED

    assert result.summary.status == "TIMED_OUT"

    assert token.is_cancelled is True

    assert marker.exists()

    assert marker.read_text(encoding="utf-8") == "cleanup completed"

    assert not any(
        step_result.name == "should_not_run" and step_result.attempts > 0
        for step_result in result.step_results
    )

    report_path = Path(result.artifact_dir) / "result.json"
    saved = json.loads(report_path.read_text(encoding="utf-8"))

    assert saved["summary"]["status"] == "TIMED_OUT"
    assert saved["metadata"]["cancel_requested"] is True
    assert saved["metadata"]["cancel_reason"] == "run_timeout"
    assert saved["metadata"]["run_timed_out"] is True
    assert result.metadata.run_timed_out is True
    assert saved["metadata"]["run_timeout_seconds"] == config.run_timeout_seconds

    saved_scenario = next(
        step_result
        for step_result in saved["step_results"]
        if step_result["name"] == "long_running"
    )

    assert saved_scenario["attempts"] == 1
    assert saved_scenario["cancelled"] is True
    assert len(saved_scenario["attempt_results"]) == 1

    saved_attempt = saved_scenario["attempt_results"][0]

    assert saved_attempt["attempt"] == 1
    assert saved_attempt["success"] is False
    assert saved_attempt["cancelled"] is True
    assert saved_attempt["timed_out"] is False
    assert saved_attempt["failure_type"] == "cancelled"


def test_run_timeout_during_retry_delay(tmp_path: Path):
    """Acceptance scenario.

    Given a failed command is waiting to retry.
    When the run deadline expires during the retry delay.
    Then the report preserves the original failed attempt without adding a cancelled attempt.
    """

    project_root = Path(__file__).resolve().parents[2]

    fixture_script = project_root / "tests" / "fixtures" / "long_running.py"

    assert fixture_script.exists()

    marker = tmp_path / "cleanup.txt"

    python = shlex.quote(sys.executable)

    marker_path = repr(str(marker))

    cleanup_command = f"{python} -c " + shlex.quote(
        "from pathlib import Path; "
        f"Path({marker_path}).write_text("
        "'cleanup completed', "
        "encoding='utf-8')"
    )

    config = RunnerConfig(
        test_case=DeviceTestCase(
            id="run_timeout_001",
            name="run_timeout_001",
            description="Run-level timeout test",
        ),
        device=DeviceInfo(
            serial="device_001",
            product="pixel",
            build="build_001",
        ),
        run_timeout_seconds=0.3,
        retry=RetryConfig(
            max_attempts=3,
            delay_seconds=2,
            retry_on=[FailureType.PROCESS_ERROR],
        ),
        lifecycle=LifecycleConfig(
            global_setup=LifecycleSteps(steps=[]),
            setup=LifecycleSteps(steps=[]),
            scenario=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="exit_command",
                        type="command",
                        command="exit 1",
                        timeout_second=30,
                    ),
                ]
            ),
            teardown=LifecycleSteps(steps=[]),
            global_teardown=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="cleanup",
                        type="command",
                        command=cleanup_command,
                        timeout_second=10,
                    )
                ]
            ),
        ),
        artifact=ArtifactConfig(output_dir=str(tmp_path)),
    )

    classifier = FailureClassifier()

    runner = DeviceTestRunner(
        executor=SubprocessExecutor(
            project_directory=project_root,
            failure_classifier=classifier,
            process_terminator=ProcessTerminator(grace_period_seconds=0.2),
        ),
        artifact_manager=ArtifactManager(tmp_path),
        artifact_validator=ArtifactValidator(),
        failure_classifier=classifier,
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config=config, cancellation_token=CancellationToken())

    scenario_result = next(
        step_result for step_result in result.step_results if step_result.name == "exit_command"
    )

    assert scenario_result.attempts == 1
    assert scenario_result.attempt_results[0].failure_type == FailureType.PROCESS_ERROR
    assert scenario_result.cancelled is True

    assert result.summary.status == "TIMED_OUT"

    assert marker.exists()

    report_path = Path(result.artifact_dir) / "result.json"
    saved = json.loads(report_path.read_text(encoding="utf-8"))

    assert saved["summary"]["status"] == "TIMED_OUT"
    assert saved["metadata"]["cancel_requested"] is True
    assert saved["metadata"]["cancel_reason"] == "run_timeout"
    assert saved["metadata"]["run_timed_out"] is True
    assert result.metadata.run_timed_out is True
    assert saved["metadata"]["run_timeout_seconds"] == config.run_timeout_seconds

    saved_scenario = next(
        step_result
        for step_result in saved["step_results"]
        if step_result["name"] == "exit_command"
    )

    assert saved_scenario["attempts"] == 1
    assert saved_scenario["cancelled"] is True
    assert len(saved_scenario["attempt_results"]) == 1

    saved_attempt = saved_scenario["attempt_results"][0]

    assert saved_attempt["attempt"] == 1
    assert saved_attempt["success"] is False
    assert saved_attempt["cancelled"] is False
    assert saved_attempt["timed_out"] is False
    assert saved_attempt["failure_type"] == "process_error"


def test_run_timeout_during_setup_runs_cleanup(
    tmp_path: Path,
):
    """Acceptance scenario.

    Given setup runs a long command after successful global setup.
    When the run deadline interrupts setup.
    Then scenario is skipped and both teardown markers are written with TIMED_OUT status.
    """
    project_root = Path(__file__).resolve().parents[2]

    fixture_script = project_root / "tests" / "fixtures" / "long_running.py"

    assert fixture_script.exists()

    python = shlex.quote(sys.executable)

    fixture = shlex.quote(str(fixture_script))

    teardown_marker = tmp_path / "teardown.txt"

    global_teardown_marker = tmp_path / "global_teardown.txt"

    scenario_marker = tmp_path / "scenario.txt"

    def marker_command(
        path: Path,
        content: str,
    ) -> str:
        return f"{python} -c " + shlex.quote(
            "from pathlib import Path; "
            f"Path({str(path)!r}).write_text("
            f"{content!r}, "
            "encoding='utf-8')"
        )

    config = RunnerConfig(
        test_case=DeviceTestCase(
            id="run_timeout_setup",
            name="run_timeout_setup",
            description=("Run timeout during setup"),
        ),
        device=DeviceInfo(
            serial="device_001",
            product="pixel",
            build="build_001",
        ),
        run_timeout_seconds=0.3,
        retry=RetryConfig(
            max_attempts=1,
            delay_seconds=0,
            retry_on=[],
        ),
        lifecycle=LifecycleConfig(
            global_setup=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="global_setup",
                        type="command",
                        command="true",
                        timeout_second=10,
                    )
                ]
            ),
            setup=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="long_setup",
                        type="command",
                        command=(f"{python} {fixture}"),
                        timeout_second=30,
                    )
                ]
            ),
            scenario=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="scenario",
                        type="command",
                        command=marker_command(
                            scenario_marker,
                            "scenario ran",
                        ),
                        timeout_second=10,
                    )
                ]
            ),
            teardown=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="teardown",
                        type="command",
                        command=marker_command(
                            teardown_marker,
                            "teardown completed",
                        ),
                        timeout_second=10,
                    )
                ]
            ),
            global_teardown=LifecycleSteps(
                steps=[
                    LifecycleStepContent(
                        name="global_teardown",
                        type="command",
                        command=marker_command(
                            global_teardown_marker,
                            "global teardown completed",
                        ),
                        timeout_second=10,
                    )
                ]
            ),
        ),
        artifact=ArtifactConfig(
            output_dir=str(tmp_path),
        ),
    )

    classifier = FailureClassifier()

    runner = DeviceTestRunner(
        executor=SubprocessExecutor(
            project_directory=project_root,
            failure_classifier=classifier,
            process_terminator=(
                ProcessTerminator(
                    grace_period_seconds=0.2,
                )
            ),
        ),
        artifact_manager=ArtifactManager(tmp_path),
        artifact_validator=ArtifactValidator(),
        failure_classifier=classifier,
        reporter=JsonReporter(),
        show_console_output=False,
    )

    token = CancellationToken()

    result = runner.run(
        config=config,
        cancellation_token=token,
    )

    assert token.is_cancelled is True

    assert token.reason == CancellationReason.RUN_TIMEOUT

    assert result.summary.status == "TIMED_OUT"

    #
    # Setup was actually interrupted.
    #
    setup_result = next(
        step_result for step_result in result.step_results if step_result.name == "long_setup"
    )

    assert setup_result.attempts == 1
    assert setup_result.cancelled is True

    assert setup_result.attempt_results[0].failure_type == FailureType.CANCELLED

    #
    # Scenario must never start.
    #
    assert scenario_marker.exists() is False

    #
    # Cleanup must still happen.
    #
    assert teardown_marker.exists() is True

    assert teardown_marker.read_text(encoding="utf-8") == "teardown completed"

    assert global_teardown_marker.exists() is True

    assert global_teardown_marker.read_text(encoding="utf-8") == "global teardown completed"
