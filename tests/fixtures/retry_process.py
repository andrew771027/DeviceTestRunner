import os
import sys
import subprocess
import time
from pathlib import Path

def main() -> int: 

    run_dir = Path(os.environ["RUN_ARTIFACT_DIR"])

    counter_file = run_dir / "retry_process_counter.txt"

    #
    # 判斷現在是第幾次 attempt
    #
    if counter_file.exists():
        attempt = int(counter_file.read_text(encoding="utf-8").strip() + 1)
    else:
        attempt = 1

    counter_file.write_text(str(attempt), encoding="utf-8")

    print(f"fixture attempt={attempt}", flush=True)

    #
    # -----------------------------------------
    # Attempt 1
    # -----------------------------------------
    #
    # 故意執行很久，
    # 讓 Device Test Runner Timeout。
    #
    if attempt == 1:
        #
        # Record fixture PID.
        #
        fixture_pid_file = run_dir / f"attempt_{attempt}.pid"

        fixture_pid_file.write_text(str(os.getpid()), encoding="utf-8")

        print(f"attempt {attempt} pid={os.getpid()}", flush=True)

        print(f"attempt {attempt} waiting for timeout", flush=True)

        #
        # Start a child process.
        #
        child = subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "import time; "
                    "time.sleep(30)"
                ),
            ]
        )

        child_pid_file = (
            run_dir
            / "attempt_1_child.pid"
        )

        child_pid_file.write_text(
            str(child.pid),
            encoding="utf-8",
        )

        print(
            (
                f"attempt {attempt} pid="
                f"{os.getpid()}"
            ),
            flush=True,
        )

        print(
            (
                f"attempt {attempt} child pid="
                f"{child.pid}"
            ),
            flush=True,
        )

        #
        # Parent 也保持 running，
        # 等 DTR timeout。
        #
        time.sleep(30)

        #
        # 正常情況不應該跑到這裡
        #
        print(f"attempt {attempt} unexpectedly finished", flush=True)

        return 1

    # -----------------------------------------
    # Attempt 2
    # -----------------------------------------
    #
    # 第二次直接成功
    #
    if attempt == 2:
        print(f"attempt {attempt} pid={os.getpid()}", flush=True)

        print(f"attempt {attempt} success", flush=True)

        return 0

    print(f"Unexpected attempt={attempt}", file=sys.stderr, flush=True)

    return 1

if __name__ == "__main__":
    sys.exit(main())