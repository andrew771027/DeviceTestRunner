import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "Usage: orphan_process.py <child_pid_file>",
            file=sys.stderr,
        )
        return 1

    child_pid_file = Path(sys.argv[1])

    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            ("import time; " "time.sleep(30)"),
        ]
    )

    child_pid_file.write_text(
        str(child.pid),
        encoding="utf-8",
    )

    print(
        f"child pid={child.pid}",
        flush=True,
    )

    #
    # Important:
    # parent exits immediately.
    #
    # Child remains in the same process group
    # because it does NOT call setsid().
    #
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
