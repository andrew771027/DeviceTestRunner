import signal
import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock

import pytest

from runner.artifact import ArtifactManager
from runner.cancellation import CancellationToken
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.models import FailureType, LifecycleStepContent
from runner.process import ProcessTerminator

PROJECT_ROOT = Path(__file__).resolve().parent


@pytest.mark.parametrize(
    argnames="test_case_id, step, stage, attempt",
    argvalues=(
        [
            (
                "test_case_001",
                LifecycleStepContent(
                    name="test",
                    type="command",
                    command="echo 'Hello World'",
                    timeout_second=1,
                ),
                "test_stage",
                1,
            ),
        ]
    ),
)
def test_subprocess_executor_return_success(tmp_path, test_case_id, step, stage, attempt):
    """Acceptance scenario.

    Given a command prints Hello World and exits zero.
    When the executor runs it with an active token.
    Then success is true, cancellation and timeout are false, and stdout matches its log.
    """
    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT,
        failure_classifier=FailureClassifier(),
        process_terminator=ProcessTerminator(),
    )

    token = CancellationToken()

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage=stage,
        step_name=step.name,
        attempt=attempt,
        show_console=False,
    )

    with log_writer:
        result = executor.execute(
            step=step,
            stage=stage,
            attempt=attempt,
            log_writer=log_writer,
            working_directory=run_dir,
            cancellation_token=token,
        )

    assert result.attempt == attempt
    assert result.exit_code == 0
    assert result.passed is True
    assert result.success is True
    assert result.cancelled is False
    assert result.timed_out is False

    assert log_writer.stdout_path.read_text(encoding="utf-8") == result.stdout
    assert result.stdout == "Hello World\n"

    assert log_writer.stderr_path.read_text(encoding="utf-8") == result.stderr
    assert result.stderr == ""


@pytest.mark.parametrize(
    argnames="test_case_id, step, stage, attempt",
    argvalues=[
        (
            "test_case_001",
            LifecycleStepContent(
                name="test failed",
                type="command",
                command=f'{sys.executable} -c "import sys; sys.exit(1)"',
                timeout_second=1,
            ),
            "test_stage",
            1,
        ),
    ],
)
def test_subprocess_executor_failure(tmp_path, test_case_id, step, stage, attempt):
    """Acceptance scenario.

    Given a command exits with code one.
    When the executor runs it.
    Then the unsuccessful result retains the exit code and captured logs.
    """
    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT,
        failure_classifier=FailureClassifier(),
        process_terminator=ProcessTerminator(),
    )

    artifact_manager = ArtifactManager(tmp_path)

    token = CancellationToken()

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage=stage,
        step_name=step.name,
        attempt=attempt,
        show_console=False,
    )

    with log_writer:
        result = executor.execute(
            step=step,
            stage=stage,
            attempt=attempt,
            log_writer=log_writer,
            working_directory=run_dir,
            cancellation_token=token,
        )

    assert result.attempt == attempt
    assert result.exit_code == 1
    assert result.success is False
    assert result.passed is False

    assert log_writer.stdout_path.read_text(encoding="utf-8") == result.stdout
    assert result.stdout == ""

    assert log_writer.stderr_path.read_text(encoding="utf-8") == result.stderr
    assert result.stderr == ""


@pytest.mark.parametrize(
    argnames="tase_case_id, step, stage, attempt",
    argvalues=[
        (
            "test_case_001",
            LifecycleStepContent(
                name="timeout_test",
                type="command",
                command="echo 'Hello World'",
                timeout_second=5,
            ),
            "test_stage",
            1,
        )
    ],
)
def test_subprocess_executor_polls_completed_subprocess(
    tmp_path, monkeypatch, tase_case_id, step, stage, attempt
):
    """Acceptance scenario.

    Given a mocked process is already complete and supplies stdout.
    When the executor starts and polls it.
    Then shell options, environment, working directory and captured output match the contract.
    """
    mocked_process = Mock()

    mocked_process.stdout = StringIO("Hello World\n")
    mocked_process.stderr = StringIO("")
    mocked_process.poll.return_value = 0
    mocked_process.returncode = 0

    mocked_popen = Mock(return_value=mocked_process)

    monkeypatch.setattr("runner.executor.subprocess.Popen", mocked_popen)

    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT,
        failure_classifier=FailureClassifier(),
        process_terminator=ProcessTerminator(),
    )

    token = CancellationToken()

    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=tase_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage=stage,
        step_name=step.name,
        attempt=attempt,
        show_console=False,
    )

    with log_writer:
        result = executor.execute(
            step=step,
            stage=stage,
            attempt=attempt,
            log_writer=log_writer,
            working_directory=run_dir,
            cancellation_token=token,
        )

    mocked_popen.assert_called_once()
    args, kwargs = mocked_popen.call_args

    assert args == (step.command,)
    assert kwargs["shell"] is True
    assert kwargs["cwd"] == str(run_dir)
    assert kwargs["env"]["DEVICE_TEST_RUNNER_ROOT"] == str(PROJECT_ROOT.resolve())
    assert kwargs["env"]["RUN_ARTIFACT_DIR"] == str(run_dir.resolve())
    assert kwargs["stdout"] == subprocess.PIPE
    assert kwargs["stderr"] == subprocess.PIPE
    assert kwargs["text"] is True
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["errors"] == "replace"
    assert kwargs["bufsize"] == 1

    mocked_process.poll.assert_called_with()
    mocked_process.wait.assert_not_called()

    assert result.exit_code == 0
    assert result.stdout == "Hello World\n"
    assert result.stderr == ""

    assert log_writer.stdout_path.read_text(encoding="utf-8") == "Hello World\n"
    assert log_writer.stderr_path.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    argnames="test_case_id, step, stage, attempt",
    argvalues=[
        (
            "test_case_001",
            LifecycleStepContent(
                name="slow_step",
                type="command",
                command="slow command",
                timeout_second=5,
            ),
            "test_stage",
            1,
        )
    ],
)
def test_subprocess_executor_raised_timeout_error(
    tmp_path, monkeypatch, test_case_id, step, stage, attempt
):
    """Acceptance scenario.

    Given a mocked process remains running past the configured timeout.
    When the executor polls it.
    Then the unsuccessful result records TIMEOUT, timed_out true and cancelled false.
    """

    mocked_process = Mock()

    # Reader threads 會讀取這兩個 stream。
    mocked_process.stdout = StringIO("")
    mocked_process.stderr = StringIO("")

    # 終止前 poll() 回傳 None；terminator 負責更新終止後的狀態。
    mocked_process.poll.return_value = None

    mocked_terminator = Mock(spec=ProcessTerminator)

    def terminate_process_group(process):
        # 模擬 process 收到 SIGTERM 後結束。
        # 被 signal 終止時，returncode 會是負的 signal 編號。
        process.returncode = -signal.SIGTERM
        process.poll.return_value = process.returncode

    # Executor 呼叫清理時，就執行上面的函式更新假 process 的狀態。
    mocked_terminator.terminate_process_group.side_effect = terminate_process_group

    # 依序模擬開始時間、逾時檢查時間與結束時間，避免實際等待。
    monkeypatch.setattr(
        "runner.executor.time.perf_counter",
        Mock(side_effect=[0, step.timeout_second, step.timeout_second]),
    )

    mocked_process.returncode = None

    mocked_popen = Mock(return_value=mocked_process)

    monkeypatch.setattr("runner.executor.subprocess.Popen", mocked_popen)

    artifact_manager = ArtifactManager(tmp_path)

    token = CancellationToken()

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage=stage,
        step_name=step.name,
        attempt=attempt,
        show_console=False,
    )

    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT,
        failure_classifier=FailureClassifier(),
        process_terminator=mocked_terminator,
    )

    with log_writer:
        result = executor.execute(
            step=step,
            stage=stage,
            attempt=attempt,
            log_writer=log_writer,
            working_directory=run_dir,
            cancellation_token=token,
        )

    mocked_popen.assert_called_once()

    assert result.attempt == 1
    assert result.success is False
    assert result.exit_code == -signal.SIGTERM
    assert result.passed is False

    assert log_writer.stdout_path.read_text(encoding="utf-8") == result.stdout
    assert result.stdout == ""
    assert log_writer.stderr_path.read_text(encoding="utf-8") == result.stderr
    assert result.stderr == ""

    assert result.timed_out is True
    assert result.cancelled is False
    assert result.failure_type == FailureType.TIMEOUT
    assert result.error == f"Command timeout after {step.timeout_second}"
    mocked_terminator.terminate_process_group.assert_called_once_with(mocked_process)
