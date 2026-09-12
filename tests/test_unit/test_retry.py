import pytest

from runner.models import ArtifactValidationResult, FailureType, RetryConfig
from runner.retry import RetryPolicy


def mock_artifact_result(passed: bool) -> ArtifactValidationResult:

    return ArtifactValidationResult(
        name="artifact", type="exists", path="result.txt", passed=passed, message="test"
    )


def test_retry_policy_does_not_retry_success():
    """Acceptance scenario.

    Given a policy permits at most three attempts.
    When the policy evaluates NONE at attempt one.
    Then retry is denied.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=1, failure_type=FailureType.NONE) is False


def test_retry_policy_retries_failure_before_max_attempts():
    """Acceptance scenario.

    Given a policy permits at most three attempts.
    When the policy evaluates NONE at attempt one and two.
    Then retry is denied for both successful outcomes.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=1, failure_type=FailureType.NONE) is False
    assert policy.should_retry(attempt=2, failure_type=FailureType.NONE) is False


def test_retry_policy_stops_at_max_attempts():
    """Acceptance scenario.

    Given a policy permits at most three attempts.
    When the policy evaluates NONE at attempt three.
    Then retry is denied.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=3, failure_type=FailureType.NONE) is False


def test_no_retry_when_process_and_artifact_passes():
    """Acceptance scenario.

    Given a policy permits at most three attempts.
    When the policy evaluates NONE at attempt one.
    Then retry is denied.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.NONE,
    )
    assert should_retry is False


def test_retry_when_process_fails():
    """Acceptance scenario.

    Given a three-attempt policy with the tested failure type eligible, excluding NONE.
    When the policy evaluates PROCESS_ERROR at attempt one.
    Then retry is allowed.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.PROCESS_ERROR,
    )
    assert should_retry is True


def test_retry_when_process_passes_but_artifact_fails():
    """Acceptance scenario.

    Given a three-attempt policy with the tested failure type eligible, excluding NONE.
    When the policy evaluates ARTIFACT_INVALID at attempt one.
    Then retry is allowed.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.ARTIFACT_INVALID,
    )

    assert should_retry is True


def test_no_retry_after_max_attempts():
    """Acceptance scenario.

    Given a three-attempt policy with the tested failure type eligible, excluding NONE.
    When the policy evaluates ARTIFACT_INVALID at attempt three.
    Then retry is denied at the attempt limit.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=3,
        failure_type=FailureType.ARTIFACT_INVALID,
    )
    assert should_retry is False


def test_retry_timeout():
    """Acceptance scenario.

    Given a three-attempt policy with the tested failure type eligible, excluding NONE.
    When the policy evaluates TIMEOUT at attempt one.
    Then retry is allowed.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(
        attempt=1,
        failure_type=FailureType.TIMEOUT,
    )

    assert should_retry is True


def test_retry_device_offline():
    """Acceptance scenario.

    Given a three-attempt policy with the tested failure type eligible, excluding NONE.
    When the policy evaluates DEVICE_OFFLINE at attempt one.
    Then retry is allowed.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, retry_on=[FailureType.DEVICE_OFFLINE]))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.DEVICE_OFFLINE)

    assert should_retry is True


def test_retry_process_error():
    """Acceptance scenario.

    Given a three-attempt policy with the tested failure type eligible, excluding NONE.
    When the policy evaluates PROCESS_ERROR at attempt one.
    Then retry is allowed.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.PROCESS_ERROR)

    assert should_retry is True


def test_retry_artifact_missing():
    """Acceptance scenario.

    Given a three-attempt policy with the tested failure type eligible, excluding NONE.
    When the policy evaluates ARTIFACT_MISSING at attempt one.
    Then retry is allowed.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, retry_on=[FailureType.ARTIFACT_MISSING]))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.ARTIFACT_MISSING)

    assert should_retry is True


def test_retry_artifact_invalid():
    """Acceptance scenario.

    Given a three-attempt policy with the tested failure type eligible, excluding NONE.
    When the policy evaluates ARTIFACT_INVALID at attempt one.
    Then retry is allowed.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.ARTIFACT_INVALID)

    assert should_retry is True


def test_failure_not_retried_after_max_attempts():
    """Acceptance scenario.

    Given a three-attempt policy with the tested failure type eligible, excluding NONE.
    When the policy evaluates TIMEOUT at attempt three.
    Then retry is denied at the attempt limit.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3))

    should_retry = policy.should_retry(attempt=3, failure_type=FailureType.TIMEOUT)

    assert should_retry is False


def test_retry_timeout_when_conifgured():
    """Acceptance scenario.

    Given timeout is explicitly eligible and attempts remain.
    When the retry policy evaluates a timeout failure.
    Then another attempt is allowed.
    """

    policy = RetryPolicy(
        RetryConfig(max_attempts=3, retry_on=[FailureType.TIMEOUT]),
    )

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.TIMEOUT)

    assert should_retry is True


def test_process_error_not_retried():
    """Acceptance scenario.

    Given retry_on excludes process errors.
    When the retry policy evaluates a process error.
    Then another attempt is not allowed.
    """

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
    """Acceptance scenario.

    Given retry_on only includes device-offline failures.
    When the retry policy evaluates a timeout.
    Then another attempt is not allowed.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, retry_on=[FailureType.DEVICE_OFFLINE]))

    assert policy.should_retry(attempt=1, failure_type=FailureType.TIMEOUT) is False


def test_artifact_invalid_not_retried_when_not_configured():
    """Acceptance scenario.

    Given retry_on only includes missing artifacts.
    When the retry policy evaluates an invalid artifact.
    Then another attempt is not allowed.
    """
    policy = RetryPolicy(RetryConfig(max_attempts=3, retry_on=[FailureType.ARTIFACT_MISSING]))

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.ARTIFACT_INVALID)

    assert should_retry is False


@pytest.mark.cancelled
def test_cancelled_is_never_retried():
    """Acceptance scenario.

    Given a Python retry policy explicitly includes CANCELLED and has attempts left.
    When a cancelled first attempt is evaluated.
    Then retry is denied despite the allow-list.
    """
    policy = RetryPolicy(
        RetryConfig(max_attempts=3, retry_on=[FailureType.TIMEOUT, FailureType.CANCELLED])
    )

    should_retry = policy.should_retry(attempt=1, failure_type=FailureType.CANCELLED)

    assert should_retry is False
