import argparse
import sys
from runner.config import ConfigLoader
from runner.executor import SubprocessExecutor
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner
from runner.artifact_validator import ArtifactValidator
from pathlib import Path

PROJECT_DIRECTORY = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    args = parser.parse_args()
    return args


def main():
    try:
        args = parse_args()

        config = ConfigLoader().load(args.config)

        runner = DeviceTestRunner(
            executor=SubprocessExecutor(project_directory=PROJECT_DIRECTORY),
            artifact_validator=ArtifactValidator(),
            reporter=JsonReporter(),
        )

        result = runner.run(config=config)

    except (OSError, KeyError, TypeError, ValueError) as e:
        print(f"Runner Error: {e}", file=sys.stderr)
        return 2

    print("==== Device Test Runner v1.1 ====")
    print(f"Test Case ID: {result.metadata.test_case_id}")
    print(f"Test Case Name: {result.metadata.test_case_name}")
    print(f"Status: {result.summary.status}")
    print()

    for step_result in result.step_results:
        print(f"[Step] {step_result.name}")
        print(f"  Success: {step_result.success}")
        print(f"  Exit Code: {step_result.exit_code}")
        print(f"  Duration: {step_result.duration_seconds:.2f}s")

        if step_result.error:
            print(f"  Error: {step_result.error}")

        print()

    if result.summary.status == "PASSED":
        return 0
    return 1


if __name__ == "__main__":
    main()
