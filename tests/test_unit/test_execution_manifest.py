import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from runner.manifest import build_manifest, save_manifest
from runner.models import DeviceInfo
from runner.config import ConfigLoader
from runner.artifact import ArtifactManager
from runner.artifact_validator import ArtifactValidator
from runner.config import ConfigLoader
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.process import ProcessTerminator
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner
from runner.variables import VariableResolutionError


def write_yaml(
    tmp_path,
    *,
    command=None,
    timeout="${{ vars.test_duration }}",
    path="${{ run.dir }}/${{ vars.output_name }}",
    variables=None,
):

    if variables is None:
        variables = {
            "repeat": 3,
            "test_duration": 5,
            "output_name": "power_result.csv",
        }

    if command is None:
        script = (
            "import csv,os,sys,pathlib;"
            "p=pathlib.Path(os.environ['RUN_ARTIFACT_DIR'])/sys.argv[1];"
            "f=p.open('w',newline='',encoding='utf-8');"
            "w=csv.writer(f);w.writerow(['repeat']);"
            "w.writerows([[i] for i in range(int(sys.argv[2]))]);f.close()"
        )

        command = (
            f"{shlex.quote(sys.executable)} -c {shlex.quote(script)}"
            " '${{ vars.output_name }}' '${{ vars.repeat }}'"
        )

    raw = {
        "test_case": {
            "id": "static_vars",
            "name": "static_vars",
            "description": "integration",
        },
        "device": {
            "serial": "device_001",
            "product": "pixel",
            "build": "test",
        },
        "variables": variables,
        "retry": {
            "max_attempts": 1,
            "delay_seconds": 0,
            "retry_on": [],
        },
        "lifecycle": {
            stage: {"steps": []}
            for stage in (
                "global_setup",
                "setup",
                "scenario",
                "teardown",
                "global_teardown",
            )
        },
        "artifact": {
            "output_dir": str(tmp_path / "runs"),
            "validation": {
                "rules": [
                    {
                        "name": "power_csv",
                        "type": "csv_content",
                        "path": path,
                        "required": True,
                        "required_columns": ["repeat"],
                        "min_rows": 3,
                    },
                ],
            },
        },
    }

    raw["lifecycle"]["scenario"]["steps"] = [
        {
            "name": "write_csv",
            "type": "command",
            "command": command,
            "timeout_second": timeout,
        },
    ]

    file = tmp_path / "sample.yml"

    file.write_text(
        yaml.safe_dump(raw),
        encoding="utf-8",
    )

    return file

def test_manifest_ene_to_end(tmp_path):
    config = ConfigLoader().load(str(write_yaml(tmp_path)))
    
    runner = DeviceTestRunner(
        executor=SubprocessExecutor(
            project_directory=tmp_path,
            failure_classifier=FailureClassifier(),
            process_terminator=ProcessTerminator(grace_period_seconds=2.0),
        ),
        artifact_manager=ArtifactManager(tmp_path / "runs"),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    path = Path(result.artifact_dir) / "execution_manifest.json"

    assert path.is_file()

    data = json.loads(path.read_text())

    assert data["schema_version"] == 1
    assert data["runner_version"] == "1.7.4"
    assert data["status"] == "COMPLETED"
    assert data["resolved_config"]["lifecycle"]["scenario"]["steps"][0]["timeout_second"] == 5
    assert data["resolved_config"]["artifact"]["validation"]["rules"][0]["path"] = str(Path(result.artifact_dir)) / "power_result.csv"
    assert len(data["resolved_config_sha256"]) == 64
    assert (Path(result.artifact_dir) / "result.json").exists() 

def test_manifest_masks_referenced_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVICE_SERIAL", "emulator-5554") 

    config = ConfigLoader().load(str(write_yaml(tmp_path)))
    
    runner = DeviceTestRunner(
        executor=SubprocessExecutor(
            project_directory=tmp_path,
            failure_classifier=FailureClassifier(),
            process_terminator=ProcessTerminator(grace_period_seconds=2.0),
        ),
        artifact_manager=ArtifactManager(tmp_path / "runs"),
        artifact_validator=ArtifactValidator(),
        failure_classifier=FailureClassifier(),
        reporter=JsonReporter(),
        show_console_output=False,
    )

    result = runner.run(config)

    manifest_text = (Path(result.artifact_dir) / "execution_manifest.json").read_text()

    assert "emulator-5554" not in manifest_text
    assert "[READACTED:env.DEVICE_SERIAL]" in manifest_text
    # Existing result.json still contains serial; manifest redaction does not secure all outputs.

def test_hash_is_stable_for_same_config(tmp_path):
    config = ConfigLoader().load(str(write_yaml(tmp_path)))

    first = build_manifest(original_config=config, 
                           resolved_config=config,
                           environment={}, 
                           run_dir=tmp_path, 
                           runner_version="1.7.4",
                           )

    second = build_manifest(original_config=config,
                            resolved_config=config,
                            environment={},
                            run_dir=tmp_path,
                            runner_version="1.7.4",
                            )
    
    assert first["source_config_sha256"] == second["source_config_sha256"]
    assert first["resolved_config_sha256"] == second["resolved_config_sha256"]


def test_hash_changes_when_repeat_changes(tmp_path):
    config = ConfigLoader().load(str(write_yaml(tmp_path)))

    updated = replace(config, variables={**config.variables, "repeat": 4},)

    first = build_manifest(original_config=config,
                           resolved_config=config,
                           environment={},
                           run_dir=tmp_path,
                           runner_version="1.7.4",
                           )

    second = build_manifest(original_config=updated,
                            resolved_config=updated,
                            environment={},
                            run_dir=tmp_path,
                            runner_version="1.7.4",
                            )

    assert first["source_config_sha256"] != second["source_config_sha256"]

def test_atomic_save_replaces_existing(tmp_path):
    save_manifest(manifest={"status": "PREPARED"}, run_dir=tmp_path,)

    save_manifest(manifest={"status": "COMPLETED"}, run_dir=tmp_path,)

    assert json.loads((tmp_path / "execution_manifest.json").read_text())["status"] == "COMPLETED"
    
    assert not list(tmp_path.glob(".manifest-*.tmp"))


def test_manifest_fails_on_non_dataclass(tmp_path):
    with pytest.raises(TypeError):
        build_manifest(original_config={},
                       resolved_config={},
                       environment={},
                       run_dir=tmp_path,
                       runner_version="1.7.4",
                    )