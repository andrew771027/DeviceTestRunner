from runner.models import RetryConfig, ArtifactValidationResult

class RetryPolicy:

    def __init__(self, config: RetryConfig):
        self.config = config

    def should_retry(self, 
                    attempt: int, 
                    process_success: bool,
                    artifact_results: list[ArtifactValidationResult]) -> bool:

        if attempt >= self.config.max_attempts:
            return False

        if not process_success:
            return True

        artifact_failed = any(not result.passed for result in artifact_results)

        if artifact_failed:
            return True
        
        return False
    
    @property
    def delay_seconds(self) -> float:
        return self.config.delay_seconds
