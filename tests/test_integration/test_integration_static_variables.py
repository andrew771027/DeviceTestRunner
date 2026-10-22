import json
import shlex
import sys
from pathlib import Path

import pytest
import yaml

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


def test_yaml_to_subprocess_artifact_and_json_report(tmp_path: Path):
    """
    Given YAML templates and a real subprocess that writes CSV rows.
    When the runner resolves and executes the configuration.
    Then CSV validation and JSON status pass while original templates remain unchanged.
    """
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

    original_command = config.lifecycle.scenario.steps[0].command

    original_path = config.artifact.validation.rules[0].path

    assert "${{ vars.repeat }}" in original_command

    assert "${{ run.dir }}" in original_path

    result = runner.run(config)

    run_dir = Path(result.artifact_dir)

    csv_path = run_dir / "power_result.csv"

    assert csv_path.exists()

    assert len(csv_path.read_text().splitlines()) == 4

    assert result.step_results[0].success

    assert "power_result.csv" in result.step_results[0].command

    assert result.artifact_validation_results[0].passed

    assert result.artifact_validation_results[0].path == str(csv_path)

    assert result.summary.status == "PASSED"

    report = json.loads((run_dir / "result.json").read_text())

    assert report["summary"]["status"] == "PASSED"

    assert config.lifecycle.scenario.steps[0].command == original_command

    assert config.artifact.validation.rules[0].path == original_path


@pytest.mark.parametrize(
    "field, value, match",
    [
        ("command", "echo '${{ vars.unknown }}'", "undefined variable"),
        ("timeout", "${{ vars.output_name }}", "finite positive number"),
        ("path", "${{ vars.missing }}", "undefined variable"),
    ],
)
def test_invalid_template_fails_before_executor(tmp_path: Path, field, value, match):
    """
    Given an invalid command, timeout or validation path template.
    When the runner resolves the loaded configuration.
    Then VariableResolutionError occurs without CSV or JSON report output.
    """
    config = ConfigLoader().load(str(write_yaml(tmp_path, **{field: value})))

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

    with pytest.raises(VariableResolutionError, match=match):
        runner.run(config)

    assert not list((tmp_path / "runs").rglob("result.json"))
    assert not list((tmp_path / "runs").rglob("*.csv"))


def test_config_rejects_recursive_variable(tmp_path):
    """
    Given YAML containing a variable that references another variable.
    When ConfigLoader loads the YAML.
    Then VariableResolutionError rejects the recursive definition.
    """
    config_path = write_yaml(
        tmp_path,
        variables={
            "repeat": 3,
            "test_duration": 5,
            "output_name": "${{ vars. repeat }}",
        },
    )

    with pytest.raises(VariableResolutionError, match="recursive"):
        ConfigLoader().load(str(config_path))


def test_two_runs_resolve_distinct_run_dirs(tmp_path):
    """
    Given one unresolved configuration and a real CSV-producing executor.
    When the runner executes that configuration twice.
    Then each distinct run directory contains its own CSV artifact.
    """
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

    first = runner.run(config)

    second = runner.run(config)

    assert first.artifact_dir != second.artifact_dir

    assert Path(first.artifact_dir, "power_result.csv").exists()

    assert Path(second.artifact_dir, "power_result.csv").exists()

def test_environment_serial_from_yaml_to_report(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVICE_SERIAL", "pixel-lab-007")
    
    yaml_path = write_yaml(tmp_path)

    raw = yaml.safe_load(yaml_path.read_text())

    raw["device"]["serial"] = "${{ env.DEVICE_SERIAL }}"

    yaml_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    config = ConfigLoader().load(str(yaml_path))

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

    assert config.device.serial == "${{ env.DEVICE_SERIAL }}"

    result = runner.run(config=config)

    assert result.metadata.device_serial == "pixel-lab-007"

    assert result.summary.status == "PASSED"

    report = json.loads((Path(result.artifact_dir) / "result.json").read_text())

    assert report["metadata"]["device_serial"] == "pixel-lab-007"

def test_missing_env_prevents_run_directory_creation(tmp_path, monkeypatch):
    monkeypatch.delenv("DEVICE_SERIAL", raising=False)

    yaml_path = write_yaml(tmp_path)

    raw = yaml.safe_load(yaml_path.read_text())

    raw["device"]["serial"] = "${{ env.DEVICE_SERIAL }}"

    yaml_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    config = ConfigLoader().load(str(yaml_path))

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

    with pytest.raises(VariableResolutionError, match="undefined environment variable"):

        runner.run(config)
    
    assert not list((tmp_path / "runs").iterdir())