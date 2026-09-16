import subprocess
import time
from runner.process import ProcessTerminator

def test_terminated_process_does_not_need_cleanup():

    process = subprocess.Popen(
        ["true"],
        start_new_session=True,
    )

    process.wait()

    process_terminator = ProcessTerminator()

    result = process_terminator.terminate_process_group(process)

    assert result.terminated is False
    assert result.killed is False
    assert result.return_code == 0

def test_process_group_terminates_gracefully():

    process = subprocess.Popen(
        [
            "python",
            "-c",
            (
                "import time; "
                "time.sleep(30)"
            ),
        ],
        start_new_session=True
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
            "python",
            "-c",
            command,
        ],

        stdout=subprocess.PIPE,
        text=True,
        start_new_session=True
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