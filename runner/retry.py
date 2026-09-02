from runner.models import ArtifactValidationResult, FailureType, RetryConfig


class RetryPolicy:

    def __init__(self, config: RetryConfig):
        self.config = config

    def should_retry(self, attempt: int, failure_type: FailureType) -> bool:

        # 已經成功
        if failure_type == FailureType.NONE:
            return False

        # 已經最大 attempt
        if attempt >= self.config.max_attempts:
            return False

        # Config-Driven Decision
        if failure_type not in self.config.retry_on:
            return False

        return failure_type in self.RETRYABLE_FAILURES

    @property
    def delay_seconds(self) -> float:
        return self.config.delay_seconds
