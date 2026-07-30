from pathlib import Path

import pytest

from runner.artifact import ArtifactManager


@pytest.mark.parametrize(
    argnames="test_case_id, stage, step_name",
    argvalues=[("test_case_001", "test_stage", "test_step")],
)
def test_writer_displays_stdout_on_console(tmp_path: Path, capsys, test_case_id, stage, step_name):

    artifact_manager = ArtifactManager(output_dir=tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir, stage=stage, step_name=step_name, show_console=True
    )

    with log_writer:
        log_writer.write_stdout("Hello World\n")

    captured = capsys.readouterr()

    assert captured.out == (f"[{stage}]" f"[{step_name}]" "[stdout] " "Hello World\n")

    assert captured.err == ""


@pytest.mark.parametrize(
    argnames="test_case_id, stage, step_name",
    argvalues=[("test_case_001", "test_stage", "test_step")],
)
def test_writer_displays_stderr_on_console(tmp_path: Path, capsys, test_case_id, stage, step_name):

    artifact_manager = ArtifactManager(output_dir=tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir, stage=stage, step_name=step_name, show_console=True
    )

    with log_writer:
        log_writer.write_stderr("Hello World\n")

    captured = capsys.readouterr()

    assert captured.out == ""

    assert captured.err == (f"[{stage}]" f"[{step_name}]" "[stderr] " "Hello World\n")
