import argparse
import sys
import signal
from pathlib import Path

from runner.artifact import ArtifactManager
from runner.artifact_validator import ArtifactValidator
from runner.config import ConfigLoader
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner
from runner.cancellation import CancellationToken
from runner.process import ProcessTerminator

PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    args = parser.parse_args()
    return args


class SignalCancellationHandler:
    def __init__(self, token: CancellationToken):
        self.token = token
        self._signal_count = 0

    def handle_sigint(self, signum, frame):
        self._signal_count += 1

        if self._signal_count == 1:
            print("\nCancellaiton requested. "
                  "Cleaning up..."
                  )

            self.token.cancel()

            return

        #
        # Optional:
        # second Ctrl + C = immediate interruption
        #
        print(
            "\nForce exit requested."
        )

        raise KeyboardInterrupt

def main():

    args = parse_args()

    config = ConfigLoader().load(args.config)

    failure_classifier = FailureClassifier()

    cancellation_token = CancellationToken()

    signal_handler = SignalCancellationHandler(cancellation_token)

    old_sigint_handler = signal_handler.signal(signal.SIGINT, signal_handler.handle_sigint)
    
    process_terminator = ProcessTerminator(grace_period_seconds=2.0)

    runner = DeviceTestRunner(
        executor=SubprocessExecutor(
            project_directory=PROJECT_ROOT, failure_classifier=failure_classifier, process_terminator=process_terminator
        ),
        artifact_manager=ArtifactManager(output_dir=config.artifact.output_dir),
        artifact_validator=ArtifactValidator(),
        failure_classifier=failure_classifier,
        reporter=JsonReporter(),
    )

    try:

        result = runner.run(config=config, cancellation_token=cancellation_token)

    except KeyboardInterrupt:

        #
        # Second Ctrl + C
        #
        return 130

    finally:
        signal.signal(signal.SIGINT, old_sigint_handler)

    print(f"Status: {result.summary.status}")

    if result.summary.status == "CANCELLED":
        return 130

    if result.summary.status == "FAILED":
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
