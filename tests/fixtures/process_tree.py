import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    #
    # ------------------------------------------
    # 讀取測試傳入的參數
    # ------------------------------------------
    #
    # 同一支 script 會啟動自己，建立三層 process：
    # 0 = parent -> 1 = child -> 2 = grandchild。
    #
    run_dir = Path(sys.argv[1])
    process_level = int(sys.argv[2])
    descendant_behavior = sys.argv[3]

    # parent 正常接受 SIGTERM。
    # ignore 情境下，只有 child / grandchild 故意忽略 SIGTERM。
    if descendant_behavior == "ignore" and process_level > 0:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

    pid_file = run_dir / f"{process_level}.pid"
    pid_file.write_text(str(os.getpid()), encoding="utf-8")

    #
    # ------------------------------------------
    # 啟動下一層 process
    # ------------------------------------------
    #
    if process_level < 2:
        child_level = process_level + 1

        subprocess.Popen(
            [
                sys.executable,
                __file__,
                str(run_dir),
                str(child_level),
                descendant_behavior,
            ]
        )

        # 等下一層準備好，自己才繼續。
        # 因此 parent 寫出 0.ready 時，代表三層都已經準備完成。
        child_ready_file = run_dir / f"{child_level}.ready"

        while not child_ready_file.exists():
            time.sleep(0.01)

    #
    # ------------------------------------------
    # 輸出 log，然後等待測試終止 process
    # ------------------------------------------
    #
    print(f"stdout role={process_level}", flush=True)
    print(f"stderr role={process_level}", file=sys.stderr, flush=True)

    ready_file = run_dir / f"{process_level}.ready"
    ready_file.touch()

    time.sleep(30)
    return 0


if __name__ == "__main__":
    sys.exit(main())
