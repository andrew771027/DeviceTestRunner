import argparse
import sys
from pathlib import Path

from runner.artifact import ArtifactManager
from runner.artifact_validator import ArtifactValidator
from runner.config import ConfigLoader
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner

PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    args = parser.parse_args()
    return args


def main():

    args = parse_args()

    config = ConfigLoader().load(args.config)
    failure_classifier = FailureClassifier()
    runner = DeviceTestRunner(
        executor=SubprocessExecutor(
            project_directory=PROJECT_ROOT, failure_classifier=failure_classifier
        ),
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=failure_classifier,
        reporter=JsonReporter(),
    )

    result = runner.run(config=config)

    print(result.summary.status)


if __name__ == "__main__":
    main()
