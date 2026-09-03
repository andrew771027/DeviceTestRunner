from runner.models import ArtifactValidationResult, FailureType, RetryConfig
from runner.retry import RetryPolicy


def mock_artifact_result(passed: bool) -> ArtifactValidationResult:

    return ArtifactValidationResult(
        name="artifact", type="exists", path="result.txt", passed=passed, message="test"
    )


def test_retry_policy_does_not_retry_success():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then retry policy does not retry success.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=1, failure_type=FailureType.NONE) is False


def test_retry_policy_retries_failure_before_max_attempts():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then retry policy retries failure before max attempts.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=1, failure_type=FailureType.NONE) is False
    assert policy.should_retry(attempt=2, failure_type=FailureType.NONE) is False


def test_retry_policy_stops_at_max_attempts():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then retry policy stops at max attempts.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=3, failure_type=FailureType.NONE) is False


def test_no_retry_when_process_and_artifact_passes():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then a fully successful attempt completes without consuming another attempt.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.NONE,
    )
    assert should_retry is False


def test_retry_when_process_fails():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then retry when process fails.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.PROCESS_ERROR,
    )
    assert should_retry is True


def test_retry_when_process_passes_but_artifact_fails():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then artifact rejection can trigger a retry even when the command itself succeeds.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.ARTIFACT_INVALID,
    )

    assert should_retry is True


def test_no_retry_after_max_attempts():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then no retry after max attempts.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=3,
        failure_type=FailureType.ARTIFACT_INVALID,
    )
    assert should_retry is False


def test_retry_timeout():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then retry timeout.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.TIMEOUT,
    )

    assert should_retry is True


def test_retry_device_offline():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then retry device offline.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, retry_on=[FailureType.DEVICE_OFFLINE]))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.DEVICE_OFFLINE)

    assert should_retry is True


def test_retry_process_error():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then retry process error.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.PROCESS_ERROR)

    assert should_retry is True


def test_retry_artifact_missing():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then retry artifact missing.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, retry_on=[FailureType.ARTIFACT_MISSING]))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.ARTIFACT_MISSING)

    assert should_retry is True


def test_retry_artifact_invalid():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then retry artifact invalid.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.ARTIFACT_INVALID)

    assert should_retry is True


def test_failure_not_retried_after_max_attempts():
    """Acceptance scenario.

    Given an attempt has a failure outcome and a configured retry limit.
    When the retry policy decides whether another attempt is allowed.
    Then failure not retried after max attempts.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=3, failure_type=FailureType.TIMEOUT)

    assert should_retry is False


def test_retry_timeout_when_conifgured():

    policy = RetryPolicy(
        RetryConfig(max_attempts=3, retry_on=[FailureType.TIMEOUT]),
    )

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.TIMEOUT)

    assert should_retry is True


def test_process_error_not_retried():

    policy = RetryPolicy(
        RetryConfig(
            max_attempts=3,
            retry_on=[
                FailureType.TIMEOUT,
                FailureType.DEVICE_OFFLINE,
            ],
        )
    )

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.PROCESS_ERROR)

    assert should_retry is False


def test_timeout_not_retried_when_not_configured():
    policy = RetryPolicy(RetryConfig(max_attempts=3, retry_on=[FailureType.DEVICE_OFFLINE]))

    assert policy.should_retry(attempt=1, failure_type=FailureType.TIMEOUT) is False


def test_artifact_invalid_not_retried_when_not_configured():
    policy = RetryPolicy(RetryConfig(max_attempts=3, retry_on=[FailureType.ARTIFACT_MISSING]))

    assert policy.should_retry(attempt=1, failure_type=FailureType.ARTIFACT_INVALID) is False
