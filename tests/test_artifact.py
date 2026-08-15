from pathlib import Path

import pytest

from runner.artifact import ArtifactManager


@pytest.mark.parametrize(
    argnames="test_case_id, stage, step_name, attempt",
    argvalues=[("test_case_001", "test_stage", "test_step", 1)],
)
def test_save_log_writer_step_stdout_and_stderr(
    tmp_path: Path, test_case_id: str, stage: str, step_name: str, attempt: int
):
    artifact_manager = ArtifactManager(output_dir=tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage=stage,
        step_name=step_name,
        attempt=attempt,
        show_console=False,
    )

    with writer:
        writer.write_stdout("stdout line1\n")
        writer.write_stdout("stdout line2\n")
        writer.write_stderr("stderr line1\n")
        writer.write_stderr("stderr line2\n")

    assert writer.stdout == ("stdout line1\n" "stdout line2\n")

    assert writer.stderr == ("stderr line1\n" "stderr line2\n")

    assert writer.stdout_path.exists() and writer.stdout_path.is_file()
    assert writer.stderr_path.exists() and writer.stderr_path.is_file()

    assert writer.stdout_path.read_text(encoding="utf-8") == "stdout line1\n" "stdout line2\n"
    assert writer.stderr_path.read_text(encoding="utf-8") == "stderr line1\n" "stderr line2\n"

    assert writer.stdout_path.parent.name == step_name
    assert writer.stdout_path.name == f"attempt_{attempt}.stdout.log"

    assert writer.stderr_path.parent.name == step_name
    assert writer.stderr_path.name == f"attempt_{attempt}.stderr.log"


@pytest.mark.parametrize(
    argnames="test_case_id, stage, step_name, attempt",
    argvalues=[("test_case_001", "test_stage", "test_step", 1)],
)
def test_step_log_writer_creates_stage_dictionary(
    tmp_path: Path, test_case_id: str, stage: str, step_name: str, attempt: 1
):
    artifact_manager = ArtifactManager(output_dir=tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage=stage,
        step_name=step_name,
        attempt=attempt,
        show_console=False,
    )

    with writer:
        writer.write_stdout("done\n")

    assert writer.stdout_path.parent.name == step_name

    assert writer.stdout_path.name == f"attempt_{attempt}.stdout.log"


@pytest.mark.parametrize(
    argnames="test_case_id, stage, step_name, attempt",
    argvalues=[("test_case_001", "test_stage", "test_step", 1)],
)
def test_step_log_writer_flushes_immediately(tmp_path, test_case_id, stage, step_name, attempt):

    artifact_manager = ArtifactManager(output_dir=tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id=test_case_id)

    writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir,
        stage=stage,
        step_name=step_name,
        attempt=attempt,
        show_console=False,
    )

    with writer:
        writer.write_stdout("first line\n")

        # Writer 還沒有關閉，但資料應已經因為 flush() 寫入檔案裡。
        current_content = writer.stdout_path.read_text(encoding="utf-8")

        assert current_content == "first line\n"
