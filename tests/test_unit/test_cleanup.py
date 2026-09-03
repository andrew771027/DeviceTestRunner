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
            required=True,
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
            required=True,
        )
    ]

    artifact_manager = ArtifactManager(output_dir=tmp_path)

    artifact_manager.cleanup_validation_targets(run_dir=run_dir, rules=rules)

    assert directory.exists() is False


def test_cleanup_does_not_remove_optional_artifact(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    artifact = run_dir / "debug.log"
    artifact.write_text("diagnostic data", encoding="utf-8")

    rules = [
        ArtifactValidationRule(
            name="debug_log",
            type="exists",
            path="debug.log",
            after_step="test",
            required=False,
        )
    ]

    ArtifactManager(output_dir=tmp_path).cleanup_validation_targets(run_dir=run_dir, rules=rules)

    assert artifact.exists() is True


def test_cleanup_does_not_remove_path_outside_run_directory(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    outside_artifact = tmp_path / "outside.csv"
    outside_artifact.write_text("must remain", encoding="utf-8")

    rules = [
        ArtifactValidationRule(
            name="outside",
            type="exists",
            path=outside_artifact,
            after_step="test",
            required=True,
        )
    ]

    ArtifactManager(output_dir=tmp_path).cleanup_validation_targets(run_dir=run_dir, rules=rules)

    assert outside_artifact.exists() is True


def test_cleanup_removes_file_inside_run_directory(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    artifact = run_dir / "result.csv"
    artifact.write_text("old data", encoding="utf-8")

    rules = [
        ArtifactValidationRule(
            name="result",
            type="exists",
            path=artifact,
            after_step="test",
            required=True,
        )
    ]

    ArtifactManager(output_dir=tmp_path).cleanup_validation_targets(
        run_dir=run_dir,
        rules=rules,
    )

    assert artifact.exists() is False


def test_cleanup_resolves_relative_path_under_run_directory(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    artifact = run_dir / "result.csv"
    artifact.write_text("old data", encoding="utf-8")

    rules = [
        ArtifactValidationRule(
            name="result",
            type="exists",
            path=Path("result.csv"),
            after_step="test",
            required=True,
        )
    ]

    ArtifactManager(output_dir=tmp_path).cleanup_validation_targets(
        run_dir=run_dir,
        rules=rules,
    )

    assert artifact.exists() is False


def test_cleanup_ignores_missing_target(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    rules = [
        ArtifactValidationRule(
            name="missing",
            type="exists",
            path=Path("missing.csv"),
            after_step="test",
            required=True,
        )
    ]

    ArtifactManager(output_dir=tmp_path).cleanup_validation_targets(
        run_dir=run_dir,
        rules=rules,
    )
