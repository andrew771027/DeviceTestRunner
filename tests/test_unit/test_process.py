import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from runner.process import ProcessTerminator


def is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)

    except ProcessLookupError:
        return False

    except PermissionError:
        return True

    return True


def test_terminated_process_does_not_need_cleanup(monkeypatch):
    """Acceptance scenario.

    Given the direct process has exited with code zero and its group is gone.
    When the terminator is called.
    Then only a group probe is sent and the result reports no termination or kill.
    """
    process = subprocess.Popen(
        ["true"],
        start_new_session=True,
    )

    process.wait()

    signal_calls = []

    def fake_killpg(process_group_id, signal_number):
        signal_calls.append((process_group_id, signal_number))
        assert signal_number == 0
        raise ProcessLookupError()

    monkeypatch.setattr("runner.process.os.killpg", fake_killpg)

    process_terminator = ProcessTerminator()

    result = process_terminator.terminate_process_group(process)

    assert result.terminated is False
    assert result.killed is False
    assert result.return_code == 0
    assert signal_calls == [(process.pid, 0)]


def test_process_group_terminates_gracefully():
    """Acceptance scenario.

    Given a real process runs in a separate session.
    When the terminator sends SIGTERM.
    Then the process exits without SIGKILL.
    """
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            ("import time; " "time.sleep(30)"),
        ],
        start_new_session=True,
    )

    process_terminator = ProcessTerminator(grace_period_seconds=1.0)

    result = process_terminator.terminate_process_group(process)

    assert result.terminated is True
    assert result.killed is False
    assert process.poll() is not None


def test_process_is_killed_when_sigterm_is_ignored():
    """Acceptance scenario.

    Given a real process confirms its SIGTERM ignore handler is ready.
    When the termination grace period expires.
    Then the terminator uses SIGKILL and the process exits.
    """
    command = (
        "import signal, time;"
        "signal.signal("
        "signal.SIGTERM, "
        "signal.SIG_IGN"
        "); "
        "print('ready', flush=True);"
        "time.sleep(30)"
    )

    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            command,
        ],
        stdout=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )

    #
    # 等child 確定已經install SIGTERM handler
    #
    assert process.stdout.readline().strip() == "ready"

    process_terminator = ProcessTerminator(grace_period_seconds=0.2)

    result = process_terminator.terminate_process_group(process)

    assert result.terminated is True
    assert result.killed is True
    assert process.poll() is not None


def test_group_probe_permission_error_does_not_abort_cleanup(monkeypatch):

    #
    # 檢查 process group 時，暫時沒有權限不代表 process 已經結束。
    # 應該繼續等待，直到確認群組不存在。
    #
    """Acceptance scenario.

    Given a fake group probe raises PermissionError before reporting that the group is gone.
    When the terminator sends SIGTERM and polls the group.
    Then the probe is retried and cleanup completes without SIGKILL.
    """

    class FakeProcess:
        def __init__(self):
            self.pid = 123
            self.returncode = None
            self.poll_count = 0

        def poll(self):
            self.poll_count += 1

            # 前兩次檢查還在執行，第三次才結束。
            if self.poll_count >= 3:
                self.returncode = 0

            return self.returncode

    process = FakeProcess()

    def fake_getpgid(pid):
        assert pid == process.pid
        return 123

    signal_calls = []

    def fake_killpg(process_group_id, signal_number):
        signal_calls.append((process_group_id, signal_number))

        # 第一次送出 SIGTERM 成功，直接返回。
        # 第二次檢查暫時沒有權限，第三次確認群組已不存在。
        if len(signal_calls) == 2:
            raise PermissionError()

        if len(signal_calls) == 3:
            raise ProcessLookupError()

    monkeypatch.setattr("runner.process.os.getpgid", fake_getpgid)
    monkeypatch.setattr("runner.process.os.killpg", fake_killpg)

    process_terminator = ProcessTerminator(grace_period_seconds=1)

    result = process_terminator.terminate_process_group(process)

    assert result.terminated is True
    assert result.killed is False
    assert signal_calls == [
        (123, signal.SIGTERM),
        (123, 0),
        (123, 0),
    ]


def test_terminator_cleans_group_even_when_direct_child_has_exited(
    tmp_path: Path,
):
    """Acceptance scenario.

    Given a reaped direct child leaves a live descendant in its process group.
    When the terminator cleans the original group.
    Then the descendant exits and the result records termination.
    """
    project_root = Path(__file__).resolve().parents[2]

    fixture_script = project_root / "tests" / "fixtures" / "orphan_process.py"

    assert fixture_script.exists()

    child_pid_file = tmp_path / "child.pid"

    process = subprocess.Popen(
        [
            sys.executable,
            str(fixture_script),
            str(child_pid_file),
        ],
        start_new_session=True,
    )

    #
    # Wait for direct parent to exit.
    #
    process.wait(timeout=5)

    assert process.poll() is not None

    #
    # Fixture must have created the child.
    #
    assert child_pid_file.exists()

    child_pid = int(child_pid_file.read_text(encoding="utf-8"))

    #
    # Critical precondition:
    #
    # direct Popen process is dead,
    # but descendant is still alive.
    #
    assert is_process_alive(child_pid) is True

    terminator = ProcessTerminator(
        grace_period_seconds=0.2,
        poll_interval_seconds=0.05,
    )

    try:
        result = terminator.terminate_process_group(process)

        deadline = time.monotonic() + 2

        while is_process_alive(child_pid) and time.monotonic() < deadline:
            time.sleep(0.05)

        assert is_process_alive(child_pid) is False

        assert result.terminated is True

    finally:
        #
        # Defensive cleanup in case the
        # implementation under test is broken.
        #
        if is_process_alive(child_pid):
            try:
                os.kill(
                    child_pid,
                    9,
                )
            except ProcessLookupError:
                pass
