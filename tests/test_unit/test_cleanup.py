from pathlib import Path

from runner.artifact import ArtifactManager
from runner.models import ArtifactValidationRule


def test_cleanup_retry_artifact(tmp_path: Path):
    """Acceptance scenario.

    Given a previous attempt left retryable artifacts in the run directory.
    When retry cleanup is performed before the next attempt.
    Then the stale retry artifact file is removed while unrelated run data remains intact.
    """
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    artifact = run_dir / "results" / "power.csv"

    artifact.parent.mkdir()

    artifact.write_text("old data", encoding="utf-8")

    rules = [
        ArtifactValidationRule(
            name="power",
            type="exists",
            path="results/power.csv",
            after_step="power_test",
            retry_on_failure=True,
        )
    ]

    artifact_manager = ArtifactManager(output_dir=tmp_path)

    artifact_manager.cleanup_validation_targets(run_dir=run_dir, rules=rules)

    assert artifact.exists() is False


def test_cleanup_retry_artifact_directory(tmp_path: Path):
    """Acceptance scenario.

    Given a previous attempt left retryable artifacts in the run directory.
    When retry cleanup is performed before the next attempt.
    Then the stale retry artifact directory is removed recursively before another attempt.
    """

    run_dir = tmp_path / "run"
    run_dir.mkdir()

    directory = run_dir / "recorder"
    directory.mkdir()

    (directory / "output.log").write_text("old recorder data", encoding="utf-8")

    rules = [
        ArtifactValidationRule(
            name="recorder",
            type="directory_not_empty",
            path="recorder",
            after_step="record",
            retry_on_failure=True,
        )
    ]

    artifact_manager = ArtifactManager(output_dir=tmp_path)

    artifact_manager.cleanup_validation_targets(run_dir=run_dir, rules=rules)

    assert directory.exists() is False
