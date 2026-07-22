from pathlib import Path

import pytest

from runner.artifact import ArtifactManager


@pytest.mark.parametrize(
    argnames="test_case_id, stage, step_name, stdout, stderr",
    argvalues=[("test_case_001", "test_stage", "test_step", "Hello World", "Error Message")],
)
def test_save_step_output(
    tmp_path: Path,
    test_case_id: str,
    stage: str,
    step_name: str,
    stdout: str,
    stderr: str,
):
    artifact_manager = ArtifactManager(output_dir=tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    stdout_path = artifact_manager.save_step_stdout(
        run_dir=run_dir, stage=stage, step_name=step_name, stdout=stdout
    )

    stderr_path = artifact_manager.save_step_stderr(
        run_dir=run_dir, stage=stage, step_name=step_name, stderr=stderr
    )

    assert run_dir.exists() and run_dir.is_dir()
    assert stdout_path.exists() and stdout_path.is_file()
    assert stderr_path.exists() and stderr_path.is_file()

    assert stdout_path.read_text(encoding="utf-8") == stdout
    assert stderr_path.read_text(encoding="utf-8") == stderr

    assert stdout_path.parent.name == stage
    assert stdout_path.name == f"{step_name}.stdout.log"

    assert stderr_path.parent.name == stage
    assert stderr_path.name == f"{step_name}.stderr.log"
