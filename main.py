import argparse

from runner.config import ConfigLoader
from runner.executor import CommandStepExecutor
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = ConfigLoader().load(args.config)

    runner = DeviceTestRunner(executor=CommandStepExecutor(), reporter=JsonReporter())

    result = runner.run(config=config)

    print("==== Device Test Runner v1.1 ====")
    print(f"Test Case ID: {result.metadata.test_case_id}")
    print(f"Test Case Name: {result.metadata.test_case_name}")
    print(f"Status: {result.summary.status}")
    print()

    for step_result in result.step_results:
        print(f"[Step] {step_result.step_name}")
        print(f"  Success: {step_result.success}")
        print(f"  Exit Code: {step_result.exit_code}")
        print(f"  Duration: {step_result.duration_seconds:.2f}s")

        if step_result.error:
            print(f"  Error: {step_result.error}")

        print()


if __name__ == "__main__":
    main()
