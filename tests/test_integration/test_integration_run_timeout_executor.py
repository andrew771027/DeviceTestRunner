import sys
import time
from pathlib import Path

from runner.artifact import ArtifactManager
from runner.cancellation import CancellationReason, CancellationToken
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.models import FailureType, LifecycleStepContent
from runner.process import ProcessTerminator
from runner.run_timeout import RunTimeoutWatchdog


def test_run_timeout_cancels_running_executor(tmp_path: Path):
    """Acceptance scenario.

    Given a real long-running process has a longer step timeout than the run deadline.
    When the watchdog cancels the executor token.
    Then the process stops with CANCELLED, not step TIMEOUT, and preserves startup output.
    """
    project_root = Path(__file__).resolve().parents[2]

    fixture_script = project_root / "tests" / "fixtures" / "long_running.py"

    assert fixture_script.exists()

    token = CancellationToken()

    classifier = FailureClassifier()

    executor = SubprocessExecutor(
        project_directory=project_root,
        failure_classifier=classifier,
        process_terminator=ProcessTerminator(grace_period_seconds=0.2),
    )

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = tmp_path / "run"

    run_dir.mkdir()

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage="scenario",
        step_name="long_running",
        attempt=1,
        show_console=False,
    )

    step = LifecycleStepContent(
        name="long_running",
        type="command",
        command=(f'"{sys.executable}" {fixture_script}'),
        timeout_second=30,
    )

    watchdog = RunTimeoutWatchdog(
        timeout_seconds=0.3,
        cancellation_token=token,
    )

    started = time.monotonic()

    try:

        watchdog.start()

        with log_writer:
            result = executor.execute(
                step=step,
                stage="scenario",
                attempt=1,
                log_writer=log_writer,
                working_directory=run_dir,
                cancellation_token=token,
            )
    finally:
        watchdog.stop()

    elapsed = time.monotonic() - started

    assert token.is_cancelled is True
    assert token.reason == CancellationReason.RUN_TIMEOUT
    assert result.success is False
    assert result.cancelled is True
    assert result.timed_out is False
    assert result.failure_type == FailureType.CANCELLED
    assert "started pid=" in result.stdout
    assert elapsed < 10
