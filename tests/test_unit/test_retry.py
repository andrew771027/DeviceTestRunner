from runner.models import ArtifactValidationResult, FailureType, RetryConfig
from runner.retry import RetryPolicy


def mock_artifact_result(passed: bool) -> ArtifactValidationResult:

    return ArtifactValidationResult(
        name="artifact", type="exists", path="result.txt", passed=passed, message="test"
    )


def test_retry_policy_does_not_retry_success():
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=1, failure_type=FailureType.NONE) is False


def test_retry_policy_retries_failure_before_max_attempts():
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=1, failure_type=FailureType.NONE) is False
    assert policy.should_retry(attempt=2, failure_type=FailureType.NONE) is False


def test_retry_policy_stops_at_max_attempts():
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=3, failure_type=FailureType.NONE) is False


def test_no_retry_when_process_and_artifact_passes():
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.NONE,
    )
    assert should_retry is False


def test_retry_when_process_fails():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.PROCESS_ERROR,
    )
    assert should_retry is True


def test_retry_when_process_passes_but_artifact_fails():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.ARTIFACT_INVALID,
    )

    assert should_retry is True


def test_no_retry_after_max_attempts():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=3,
        failure_type=FailureType.ARTIFACT_INVALID,
    )
    assert should_retry is False


def test_retry_timeout():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.TIMEOUT,
    )

    assert should_retry is True


def test_retry_device_offline():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.DEVICE_OFFLINE)

    assert should_retry is True


def test_retry_process_error():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.PROCESS_ERROR)

    assert should_retry is True


def test_retry_artifact_missing():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.ARTIFACT_MISSING)

    assert should_retry is True


def test_retry_artifact_invalid():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.ARTIFACT_INVALID)

    assert should_retry is True


def test_failure_not_retried_after_max_attempts():
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=3, failure_type=FailureType.TIMEOUT)

    assert should_retry is False
