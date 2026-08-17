from runner.models import RetryConfig, ArtifactValidationResult
from runner.retry import RetryPolicy

def mock_artifact_result(passed: bool) -> ArtifactValidationResult:

    return ArtifactValidationResult(
        name="artifact",
        type="exists",
        path="result.txt",
        passed=passed,
        message="test"
    )

def test_retry_policy_does_not_retry_success():
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=1, process_success=True, artifact_results=[]) is False


def test_retry_policy_retries_failure_before_max_attempts():
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=1, process_success=False, artifact_results=[]) is True
    assert policy.should_retry(attempt=2, process_success=False, artifact_results=[]) is True


def test_retry_policy_stops_at_max_attempts():
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=3, process_success=False, artifact_results=[]) is False

def test_no_retry_when_process_and_artifact_passes():
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    should_retry = policy.should_retry(attempt=1, 
                                       process_success=True, 
                                       artifact_results=[mock_artifact_result(passed=True)],
                                       )
    assert should_retry is False

def test_retry_when_process_fails():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=1,
                                       process_success=False,
                                       artifact_results=[],
                                       )
    assert should_retry is True

def test_retry_when_process_passes_but_artifact_fails():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=1,
                                       process_success=True,
                                       artifact_results=[mock_artifact_result(passed=False)],
                                       )

    assert should_retry is True

def test_no_retry_after_max_attempts():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=3,
                                       process_success=True,
                                       artifact_results=[
                                           mock_artifact_result(passed=False)
                                       ],
                                       )
    assert should_retry is False