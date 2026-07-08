import subprocess
import time

from runner.models import ScenarioConfig, TestResult


class SubprocessScenarioExecutor:
    def run(self, test_name: str, scenario: ScenarioConfig) -> TestResult:
        start_time = time.time()

        try:

            complete = subprocess.run(
                scenario.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=scenario.timeout_second,
            )

            duration = time.time() - start_time

            return TestResult(
                test_name=test_name,
                command=scenario.command,
                success=complete.returncode == 0,
                exit_code=complete.returncode,
                duration=duration,
                stdout=complete.stdout,
                stderr=complete.stderr,
            )
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time

            return TestResult(
                test_name=test_name,
                command=scenario.command,
                success=False,
                exit_code=None,
                duration=duration,
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                error=f"Timeout after {scenario.timeout_seconds} seconds",
            )
