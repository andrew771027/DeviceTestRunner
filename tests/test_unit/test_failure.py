from runner.failure import FailureClassifier
from runner.models import ArtifactValidationResult, FailureType


def test_classifies_success_as_none():
    classifier = FailureClassifier()

    result = classifier.classify_process_failure(
        process_success=True, timed_out=False, stderr="", error=""
    )

    assert result == FailureType.NONE


def test_classifies_timeout():
    classifier = FailureClassifier()

    result = classifier.classify_process_failure(
        process_success=False, timed_out=True, stderr="", error=""
    )

    assert result == FailureType.TIMEOUT


def test_classifies_device_offline():
    classifier = FailureClassifier()

    result = classifier.classify_process_failure(
        process_success=False, timed_out=False, stderr="error: device offline", error=""
    )

    assert result == FailureType.DEVICE_OFFLINE


def test_classifies_process_error():
    classifier = FailureClassifier()

    result = classifier.classify_process_failure(
        process_success=False, timed_out=False, stderr="command", error=""
    )

    assert result == FailureType.PROCESS_ERROR


def test_classifies_artifact_missing():
    classifier = FailureClassifier()

    results = [
        ArtifactValidationResult(
            name="power",
            type="exists",
            path="power.csv",
            passed=False,
            failure_type=FailureType.ARTIFACT_MISSING,
            message="Artifact does not exists.",
        )
    ]

    result = classifier.classify_artifact_failure(results)

    assert result == FailureType.ARTIFACT_MISSING


def test_classifies_artifact_invalid():
    classifier = FailureClassifier()

    results = [
        ArtifactValidationResult(
            name="power",
            type="csv_content",
            path="power.csv",
            passed=False,
            failure_type=FailureType.ARTIFACT_INVALID,
            message="CSV missing columns",
        )
    ]

    result = classifier.classify_artifact_failure(results)

    assert result == FailureType.ARTIFACT_INVALID


def test_artifact_missing_has_priority():
    classifier = FailureClassifier()

    results = [
        ArtifactValidationResult(
            name="json",
            type="json_content",
            path="result.json",
            passed=False,
            failure_type=FailureType.ARTIFACT_INVALID,
            message="invalid",
        ),
        ArtifactValidationResult(
            name="csv",
            type="exists",
            path="power.csv",
            passed=False,
            failure_type=FailureType.ARTIFACT_MISSING,
            message="missing",
        ),
    ]

    result = classifier.classify_artifact_failure(results)

    assert result == FailureType.ARTIFACT_MISSING
