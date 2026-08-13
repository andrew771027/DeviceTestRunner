from runner.models import RetryConfig
from runner.retry import RetryPolicy


def test_retry_policy_does_not_retry_success():
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=1, success=True) is False


def test_retry_policy_retries_failure_before_max_attempts():
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=1, success=False) is True
    assert policy.should_retry(attempt=2, success=False) is True


def test_retry_policy_stops_at_max_attempts():
    policy = RetryPolicy(RetryConfig(max_attempts=3, delay_seconds=0))

    assert policy.should_retry(attempt=3, success=False) is False
