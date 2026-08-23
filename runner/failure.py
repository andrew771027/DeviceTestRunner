from typing import List

from runner.models import ArtifactValidationResult, FailureType


class FailureClassifier:

    DEVICE_OFFLINE_PATTERNS = (
        "device offline",
        "no devices/emulators found",
        "device not found",
        "device unauthorized",
    )

    def classify_process_failure(
        self,
        *,
        process_success: bool,
        time_out: bool,
        stderr: str,
        error: str,
    ) -> FailureType:

        if process_success:
            return FailureType.NONE

        if time_out:
            return FailureType.TIMEOUT

        combined_message = f"{stderr}\n{error}".lower()

        if any(pattern in combined_message for pattern in self.DEVICE_OFFLINE_PATTERNS):
            return FailureType.DEVICE_OFFLINE

        return FailureType.PROCESS_ERROR

    def classify_artifact_failure(
        self, artifact_results: List[ArtifactValidationResult]
    ) -> FailureType:

        failed_results = [result for result in artifact_results if not result.passed]

        if not failed_results:
            return FailureType.NONE

        if any(result.failure_type in FailureType.ARTIFACT_MISSING for result in artifact_results):
            return FailureType.ARTIFACT_MISSING

        return FailureType.ARTIFACT_INVALID
