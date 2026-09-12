from runner.failure import FailureClassifier
from runner.models import ArtifactValidationResult, FailureType


def test_classifies_success_as_none():
    """Acceptance scenario.

    Given a process reports success.
    When the process failure classifier evaluates it.
    Then the classification is NONE.
    """
    classifier = FailureClassifier()

    result = classifier.classify_process_failure(
        process_success=True, timed_out=False, stderr="", error=""
    )

    assert result == FailureType.NONE


def test_classifies_timeout():
    """Acceptance scenario.

    Given a failed process has timed_out set.
    When the process failure classifier evaluates it.
    Then the classification is TIMEOUT.
    """
    classifier = FailureClassifier()

    result = classifier.classify_process_failure(
        process_success=False, timed_out=True, stderr="", error=""
    )

    assert result == FailureType.TIMEOUT


def test_classifies_device_offline():
    """Acceptance scenario.

    Given a failed process reports device offline.
    When the process failure classifier evaluates the messages.
    Then the classification is DEVICE_OFFLINE.
    """
    classifier = FailureClassifier()

    result = classifier.classify_process_failure(
        process_success=False, timed_out=False, stderr="error: device offline", error=""
    )

    assert result == FailureType.DEVICE_OFFLINE


def test_classifies_process_error():
    """Acceptance scenario.

    Given a failed process has no timeout or device-offline signature.
    When the process failure classifier evaluates it.
    Then the classification is PROCESS_ERROR.
    """
    classifier = FailureClassifier()

    result = classifier.classify_process_failure(
        process_success=False, timed_out=False, stderr="command", error=""
    )

    assert result == FailureType.PROCESS_ERROR


def test_classifies_artifact_missing():
    """Acceptance scenario.

    Given validation reports a missing artifact.
    When the artifact failure classifier evaluates the results.
    Then the classification is ARTIFACT_MISSING.
    """
    classifier = FailureClassifier()

    results = [
        ArtifactValidationResult(
            name="power",
            type="exists",
            path="power.csv",
            passed=False,
            required=True,
            failure_type=FailureType.ARTIFACT_MISSING,
            message="Artifact does not exists.",
        )
    ]

    result = classifier.classify_artifact_failure(results)

    assert result == FailureType.ARTIFACT_MISSING


def test_classifies_artifact_invalid():
    """Acceptance scenario.

    Given validation reports an invalid artifact.
    When the artifact failure classifier evaluates the results.
    Then the classification is ARTIFACT_INVALID.
    """
    classifier = FailureClassifier()

    results = [
        ArtifactValidationResult(
            name="power",
            type="csv_content",
            path="power.csv",
            passed=False,
            required=True,
            failure_type=FailureType.ARTIFACT_INVALID,
            message="CSV missing columns",
        )
    ]

    result = classifier.classify_artifact_failure(results)

    assert result == FailureType.ARTIFACT_INVALID


def test_artifact_missing_has_priority():
    """Acceptance scenario.

    Given missing and invalid artifact results coexist.
    When the artifact failure classifier evaluates the results.
    Then ARTIFACT_MISSING takes priority.
    """
    classifier = FailureClassifier()

    results = [
        ArtifactValidationResult(
            name="json",
            type="json_content",
            path="result.json",
            passed=False,
            required=True,
            failure_type=FailureType.ARTIFACT_INVALID,
            message="invalid",
        ),
        ArtifactValidationResult(
            name="csv",
            type="exists",
            path="power.csv",
            passed=False,
            required=True,
            failure_type=FailureType.ARTIFACT_MISSING,
            message="missing",
        ),
    ]

    result = classifier.classify_artifact_failure(results)

    assert result == FailureType.ARTIFACT_MISSING
