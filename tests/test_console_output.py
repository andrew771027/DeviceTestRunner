from pathlib import Path
from runner.artifact import ArtifactManager

def test_writer_displays_stdout_on_console(tmp_path:Path, capsys):

    artifact_manager = ArtifactManager(output_dir=tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id="test_case_001")

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir, stage="test_stage", step_name="test_step", show_console=True
    )

    with log_writer:
        log_writer.write_stdout("Hello World\n")

    captured = capsys.readouterr()

    assert captured.out == (
        "[test_stage]"
        "[test_step]"
        "[stdout] "
        "Hello World\n"
    )

    assert captured.err == ""

def test_writer_displays_stderr_on_console(tmp_path:Path, capsys):

    artifact_manager = ArtifactManager(output_dir=tmp_path)

    run_dir = artifact_manager.create_run_directory(test_case_id="test_case_001")

    log_writer = artifact_manager.create_step_log_writer(
        run_dir=run_dir, stage="test_stage", step_name="test_step", show_console=True
    )

    with log_writer:
        log_writer.write_stderr("Hello World\n")

    captured = capsys.readouterr()

    assert captured.out == ""

    assert captured.err == (
        "[test_stage]"
        "[test_step]"
        "[stderr] "
        "Hello World\n"
    )