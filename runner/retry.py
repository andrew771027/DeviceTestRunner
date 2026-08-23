from runner.models import ArtifactValidationResult, FailureType, RetryConfig


class RetryPolicy:

    RETRYABLE_FAILURES = {
        FailureType.TIMEOUT,
        FailureType.DEVICE_OFFLINE,
        FailureType.PROCESS_ERROR,
        FailureType.ARTIFACT_MISSING,
        FailureType.ARTIFACT_INVALID,
    }

    def __init__(self, config: RetryConfig):
        self.config = config

    def should_retry(self, attempt: int, failure_type: FailureType) -> bool:

        if failure_type == FailureType.NONE:
            return False

        if attempt >= self.config.max_attempts:
            return False

        return failure_type in self.RETRYABLE_FAILURES

    @property
    def delay_seconds(self) -> float:
        return self.config.delay_seconds
