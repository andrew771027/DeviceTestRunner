from runner.models import RetryConfig


class RetryPolicy:

    def __init__(self, config: RetryConfig):
        self.config = RetryConfig

    def should_retry(self, attempt: int, success: bool) -> bool:
        if success:
            return False
        return attempt < self.config.max_attempts

    @property
    def deloay_seconds(self) -> float:
        return self.config.delay_seconds
