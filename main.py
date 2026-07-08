import argparse

from runner.config import ConfigLoader
from runner.executor import SubprocessScenarioExecutor
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = ConfigLoader().load(args.config)

    runner = DeviceTestRunner(executor=SubprocessScenarioExecutor(), reporter=JsonReporter())

    result = runner.run(config=config)

    print("==== Device Test Result ====")
    print(f"Test Name: {result.test_name}")
    print(f"Command: {result.command}")
    print(f"Success: {result.success}")
    print(f"Exit Code: {result.exit_code}")
    print(f"Duration: {result.duration}")

    if result.error:
        print(f"Error: {result.error}")


if __name__ == "__main__":
    main()
