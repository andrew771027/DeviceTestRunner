import os
import shlex
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from runner.artifact import ArtifactManager
from runner.cancellation import CancellationToken
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.models import FailureType, LifecycleStepContent
from runner.process import ProcessTerminator

PROJECT_ROOT = Path(__file__).resolve().parent


def test_executor_cancels_running_process(tmp_path: Path):
    """Acceptance scenario.

    Given a real shell command prints started and sleeps with an active token.
    When another thread cancels the token during execution.
    Then the result preserves started output and reports CANCELLED with timed_out false.
    """
    artifact_manager = ArtifactManager(tmp_path)

    run_dir = artifact_manager.create_run_directory("cancel_test")

    writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage="scenario",
        step_name="long_running",
        attempt=1,
        show_console=False,
    )

    token = CancellationToken()

    step = LifecycleStepContent(
        name="long_running",
        type="command",
        command=("echo started; " "sleep 10; " "echo finished"),
        timeout_second=30,
    )

    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT,
        failure_classifier=FailureClassifier(),
        process_terminator=ProcessTerminator(),
    )

    def cancel_soon():
        time.sleep(0.2)
        token.cancel()

    cancellation_thread = threading.Thread(target=cancel_soon)

    cancellation_thread.start()

    with writer:

        result = executor.execute(
            step=step,
            stage="scenario",
            attempt=1,
            log_writer=writer,
            working_directory=run_dir,
            cancellation_token=token,
        )

    cancellation_thread.join()

    assert result.success is False
    assert result.cancelled is True
    assert result.timed_out is False
    assert result.failure_type == FailureType.CANCELLED
    assert result.failure_type != FailureType.TIMEOUT
    assert "started" in result.stdout


def test_stdout_reader_thread_finishes_after_process_termination(tmp_path: Path):

    token = CancellationToken()

    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT,
        failure_classifier=FailureClassifier(),
        process_terminator=ProcessTerminator(grace_period_seconds=0.5),
    )

    step = LifecycleStepContent(
        name="streaming",
        type="command",
        command=("echo start; " "sleep 30"),
        timeout_second=60,
    )

    artifat_manager = ArtifactManager(tmp_path)

    run_dir = artifat_manager.create_run_directory("stream_test")

    writer = artifat_manager.create_step_log_writer(
        run_dir=run_dir,
        stage="scenario",
        step_name="streaming",
        attempt=1,
        show_console=False,
    )

    def cancel_soon():
        time.sleep(0.2)
        token.cancel()

    thread = threading.Thread(target=cancel_soon)

    thread.start()

    with writer:

        result = executor.execute(
            step=step,
            stage="scenario",
            attempt=1,
            log_writer=writer,
            working_directory=run_dir,
            cancellation_token=token,
        )

    thread.join()

    assert result.cancelled is True
    assert "start" in result.stdout


def test_stderr_is_drained_after_cancellation(tmp_path: Path):

    token = CancellationToken()

    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT,
        failure_classifier=FailureClassifier(),
        process_terminator=ProcessTerminator(grace_period_seconds=0.5),
    )

    step = LifecycleStepContent(
        name="stderr_test",
        type="command",
        command=("echo error-message >&2; " "sleep 30"),
        timeout_second=60,
    )

    artifat_manager = ArtifactManager(tmp_path)

    run_dir = artifat_manager.create_run_directory("stream_test")

    writer = artifat_manager.create_step_log_writer(
        run_dir=run_dir,
        stage="scenario",
        step_name="stderr_test",
        attempt=1,
        show_console=False,
    )

    def cancel_soon():
        time.sleep(0.2)
        token.cancel()

    thread = threading.Thread(target=cancel_soon)

    thread.start()

    with writer:

        result = executor.execute(
            step=step,
            stage="scenario",
            attempt=1,
            log_writer=writer,
            working_directory=run_dir,
            cancellation_token=token,
        )

    thread.join()

    assert result.cancelled is True
    assert "error-message" in result.stderr


def test_process_group_termination_cleans_child_processes(tmp_path: Path):

    child_pid_file = tmp_path / "child.pid"

    command = f"""
    sleep 30 &
    CHILD_PID=$!
    echo $CHILD_PID > "{child_pid_file}"
    wait $CHILD_PID
"""

    process = subprocess.Popen(
        command,
        shell=True,
        start_new_session=True,
    )

    #
    # 等child PID 寫出來
    #
    deadline = time.monotonic() + 2

    while not child_pid_file.exists():

        if time.monotonic() >= deadline:
            raise AssertionError("Child PID file was not created")

        time.sleep(0.05)

    child_pid = int(child_pid_file.read_text().strip())

    #
    # Child 一開始應該存在
    #
    os.kill(child_pid, 0)

    process_terminator = ProcessTerminator(grace_period_seconds=0.5)

    process_terminator.terminate_process_group(process)

    #
    # 給 OS 一點時間完成 process cleanup
    #
    time.sleep(0.1)

    try:

        os.kill(child_pid, 0)

        child_alive = True

    except ProcessLookupError:

        child_alive = False

    assert child_alive is False


@pytest.mark.parametrize(
    argnames="stop_reason, descendant_behavior",
    argvalues=[
        ("timeout", "default"),
        ("timeout", "ignore"),
        ("cancel", "default"),
        ("cancel", "ignore"),
    ],
)
def test_executor_cleans_entire_tree_and_drains_readers(
    tmp_path: Path, monkeypatch, stop_reason, descendant_behavior
):
    #
    # ------------------------------------------
    # 測試情境
    # ------------------------------------------
    #
    # 啟動 parent -> child -> grandchild。
    # timeout 或 cancel 後，三個 process 都必須結束。
    #
    # default: child / grandchild 正常接受 SIGTERM。
    # ignore: child / grandchild 忽略 SIGTERM，必須靠 SIGKILL 結束。
    #
    fixture_script = Path(__file__).resolve().parents[1] / "fixtures" / "process_tree.py"

    #
    # ------------------------------------------
    # 記錄真正啟動的 process 和 reader thread
    # ------------------------------------------
    #
    # 這裡沒有換成假的 process。
    # 保留原本的函式，呼叫時順便記錄物件，方便最後檢查及清理。
    #
    started_processes = []
    reader_threads = []

    original_popen = subprocess.Popen
    original_join_reader = SubprocessExecutor._join_reader_thread

    def start_and_record_process(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        started_processes.append(process)
        return process

    def join_and_record_reader(thread):
        if thread is not None:
            reader_threads.append(thread)

        original_join_reader(thread)

    monkeypatch.setattr("runner.executor.subprocess.Popen", start_and_record_process)

    # _join_reader_thread 原本是 staticmethod，替換後也維持相同用法。
    monkeypatch.setattr(
        SubprocessExecutor,
        "_join_reader_thread",
        staticmethod(join_and_record_reader),
    )

    #
    # ------------------------------------------
    # 等待 process 準備好，再發出 cancel
    # ------------------------------------------
    #
    token = CancellationToken()

    # Event 可以讓兩個 thread 通知彼此。
    # 測試結束時設為 True，讓等待中的 cancellation thread 離開。
    stop_waiting = threading.Event()
    tree_ready = threading.Event()

    def cancel_when_processes_are_ready():
        deadline = time.monotonic() + 5

        while time.monotonic() < deadline:
            if stop_waiting.is_set():
                return

            # fixture 確認三個 process 都已準備好，才會建立 0.ready。
            if (tmp_path / "0.ready").exists():
                tree_ready.set()
                token.cancel()
                return

            stop_waiting.wait(0.01)

    cancellation_thread = threading.Thread(target=cancel_when_processes_are_ready)

    #
    # ------------------------------------------
    # Config / Executor
    # ------------------------------------------
    #
    artifact_manager = ArtifactManager(tmp_path)

    writer = artifact_manager.create_step_log_writer(
        run_dir=tmp_path,
        stage="scenario",
        step_name="tree",
        attempt=1,
        show_console=False,
    )

    if stop_reason == "timeout":
        timeout_seconds = 2
    else:
        # cancel 情境保留較長 timeout，避免還沒取消就先逾時。
        timeout_seconds = 10

    # shlex.join 會處理路徑中的空白及引號。
    # exec 讓 shell 直接換成 fixture process，方便記錄 process group。
    command = shlex.join(
        ["exec", sys.executable, str(fixture_script), str(tmp_path), "0", descendant_behavior]
    )

    step = LifecycleStepContent(
        name="tree",
        type="command",
        command=command,
        timeout_second=timeout_seconds,
    )

    executor = SubprocessExecutor(
        project_directory=PROJECT_ROOT,
        failure_classifier=FailureClassifier(),
        process_terminator=ProcessTerminator(grace_period_seconds=0.2),
    )

    try:
        #
        # ------------------------------------------
        # Run
        # ------------------------------------------
        #
        if stop_reason == "cancel":
            cancellation_thread.start()

        with writer:
            result = executor.execute(
                step=step,
                stage="scenario",
                attempt=1,
                log_writer=writer,
                working_directory=tmp_path,
                cancellation_token=token,
            )

        #
        # ------------------------------------------
        # 確認取消與逾時沒有混在一起
        # ------------------------------------------
        #
        assert (tmp_path / "0.ready").exists()

        if stop_reason == "cancel":
            assert tree_ready.is_set()
            assert result.cancelled is True
            assert result.timed_out is False
            assert result.failure_type == FailureType.CANCELLED
        else:
            assert result.cancelled is False
            assert result.timed_out is True
            assert result.failure_type == FailureType.TIMEOUT

        #
        # ------------------------------------------
        # stdout / stderr reader 都必須結束
        # ------------------------------------------
        #
        assert len(reader_threads) == 2

        reader_names = []
        for thread in reader_threads:
            reader_names.append(thread.name)
            assert thread.is_alive() is False

        assert "scenario-tree-stdout" in reader_names
        assert "scenario-tree-stderr" in reader_names

        # 記憶體中的輸出，也必須完整寫入 log 檔案。
        assert writer.stdout_path.read_text(encoding="utf-8") == result.stdout
        assert writer.stderr_path.read_text(encoding="utf-8") == result.stderr

        #
        # ------------------------------------------
        # 確認每一層 process 的輸出及 PID
        # ------------------------------------------
        #
        # 0 = parent，1 = child，2 = grandchild。
        #
        for process_level in range(3):
            assert f"stdout role={process_level}" in result.stdout
            assert f"stderr role={process_level}" in result.stderr

            pid_file = tmp_path / f"{process_level}.pid"
            process_pid = int(pid_file.read_text(encoding="utf-8"))

            # 給 OS 一點時間完成回收，最多等 2 秒。
            process_alive = True
            deadline = time.monotonic() + 2

            while time.monotonic() < deadline:
                try:
                    # signal 0 只檢查 process 是否存在，不會終止它。
                    os.kill(process_pid, 0)
                except ProcessLookupError:
                    process_alive = False
                    break

                time.sleep(0.01)

            assert process_alive is False, f"Process 還沒結束：PID={process_pid}"

    finally:
        #
        # ------------------------------------------
        # 測試失敗時也要清理，避免留下背景 process
        # ------------------------------------------
        #
        stop_waiting.set()

        # ident 不是 None，代表這個 thread 曾經啟動過，才可以 join。
        if cancellation_thread.ident is not None:
            cancellation_thread.join(timeout=2)

        for process in started_processes:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                # 群組已經結束，不需要再處理。
                pass

            process.wait(timeout=2)

        for thread in reader_threads:
            thread.join(timeout=2)
