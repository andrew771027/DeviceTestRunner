import signal
import subprocess
import sys

from runner.process import ProcessTerminator


def test_terminated_process_does_not_need_cleanup(monkeypatch):

    process = subprocess.Popen(
        ["true"],
        start_new_session=True,
    )

    process.wait()

    signal_calls = []

    def fake_killpg(process_group_id, signal_number):
        signal_calls.append((process_group_id, signal_number))

    monkeypatch.setattr("runner.process.os.killpg", fake_killpg)

    process_terminator = ProcessTerminator()

    result = process_terminator.terminate_process_group(process)

    assert result.terminated is False
    assert result.killed is False
    assert result.return_code == 0
    assert signal_calls == []


def test_process_group_terminates_gracefully():

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
