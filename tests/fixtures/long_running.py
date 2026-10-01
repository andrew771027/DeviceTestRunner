import os
import time


def main() -> None:
    print(f"started pid={os.getpid()}", flush=True)

    while True:
        print(
            "still running",
            flush=True,
        )

        time.sleep(0.1)


if __name__ == "__main__":
    main()
