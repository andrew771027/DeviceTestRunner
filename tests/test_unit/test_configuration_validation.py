from dataclasses import replace

import pytest
import yaml

from runner.config import ConfigLoader
from runner.config_validation import (
    ConfigurationValidationError,
    validate_cross_fields,
    validate_schema,
)
from runner.models import (
    ArtifactConfig,
    ArtifactValidationConfig,
    ArtifactValidationRule,
    DeviceInfo,
    DeviceTestCase,
    LifecycleConfig,
    LifecycleStepContent,
    LifecycleSteps,
    RetryConfig,
    RunnerConfig,
)


def valid_raw():

    return {
        "test_case": {
            "id": "case",
            "name": "case",
            "description": "test",
        },
        "device": {
            "serial": "${{env.DEVICE_SERIAL}}",
            "product": "pixel",
            "build": "test",
        },
        "variables": {
            "repeat": 3,
            "duration": 5,
        },
        "retry": {
            "max_attempts": 1,
            "delay_seconds": 0,
            "retry_on": [],
        },
        "lifecycle": {
            "scenario": {
                "steps": [
                    {
                        "name": "power",
                        "type": "command",
                        "command": "echo ${{vars.repeat}}",
                        "timeout_second": "${{vars.duration}}",
                    },
                ],
            },
        },
        "artifact": {
            "output_dir": "./runs",
            "validation": {
                "rules": [
                    {
                        "name": "power_csv",
                        "type": "csv_content",
                        "path": "${{ run.dir }}/result.csv",
                        "after_step": "power",
                        "required_columns": [
                            "voltage",
                        ],
                    },
                ],
            },
        },
    }


def config_with_rules(*rules, steps=None):
    return RunnerConfig(
        test_case=DeviceTestCase(
            id="case",
            name="case",
            description="test",
        ),
        device=DeviceInfo(serial="serial", product="pixel", build="build"),
        lifecycle=LifecycleConfig(
            scenario=LifecycleSteps(
                steps=steps
                or [
                    LifecycleStepContent(
                        name="power",
                        type="command",
                        command="echo ok",
                        timeout_second=10,
                    ),
                ]
            )
        ),
        retry=RetryConfig(
            max_attempts=1,
            retry_on=[],
        ),
        artifact=ArtifactConfig(
            output_dir="runs",
            validation=ArtifactValidationConfig(list(rules)),
        ),
    )


def test_valid_schema():
    """
    Given a structurally valid configuration with templates and omitted stages.
    When schema validation runs.
    Then the configuration is accepted without resolving templates.
    """
    validate_schema(valid_raw())


@pytest.mark.parametrize(
    "mutate, fragment",
    [
        (lambda x: x["retry"].update(max_attempts=True), "retry.max_attempts"),
        (lambda x: x["retry"].update(delay_seconds=-1), "retry.delay_seconds"),
        (
            lambda x: x["lifecycle"]["scenario"]["steps"][0].update(timeout_second=0),
            "timeout_second",
        ),
        (
            lambda x: x["lifecycle"]["scenario"]["steps"][0].update(timeout_second="600"),
            "timeout_second",
        ),
        (
            lambda x: x["artifact"]["validation"]["rules"][0].update(required="true"),
            ".required",
        ),
        (
            lambda x: x["artifact"]["validation"]["rules"][0].update(min_rows=-1),
            ".min_rows",
        ),
        (
            lambda x: x["artifact"]["validation"]["rules"][0].update(required_columns="voltage"),
            ".required_columns",
        ),
        (
            lambda x: x["artifact"]["validation"]["rules"][0].update(typo="oops"),
            ".typo",
        ),
        (lambda x: x.update(unknown_root=123), "root.unknown_root"),
        (lambda x: x.pop("device"), "root.device"),
        (lambda x: x["lifecycle"]["scenario"].update(steps="not-a-list"), "steps"),
        (lambda x: x.update(run_timeout_seconds=False), "run_timeout_seconds"),
        (lambda x: x["variables"].update(repeat=float("inf")), "variables.repeat"),
    ],
)
def test_invalid_schema(mutate, fragment):
    """
    Given a valid configuration changed by the parameterized mutation.
    When schema validation runs.
    Then the matching field diagnostic is raised.
    """
    raw = valid_raw()
    mutate(raw)

    with pytest.raises(ConfigurationValidationError, match=fragment):
        validate_schema(raw)


def test_schema_aggregates_multiple_errors():
    """
    Given invalid retry attempts and a non-boolean required flag.
    When schema validation runs.
    Then the exception contains at least two errors.
    """
    raw = valid_raw()
    raw["retry"]["max_attempts"] = 0
    raw["artifact"]["validation"]["rules"][0]["required"] = "yes"

    with pytest.raises(ConfigurationValidationError) as caught:
        validate_schema(raw)

    assert len(caught.value.errors) >= 2


@pytest.mark.parametrize(
    "rule, fragment",
    [
        (
            ArtifactValidationRule(
                name="bad",
                type="exists",
                path="a",
                after_step="missing",
            ),
            "unknown step",
        ),
        (
            ArtifactValidationRule(
                name="bad",
                type="invalid_type",
                path="a",
            ),
            "unsupported validation type",
        ),
        (
            ArtifactValidationRule(
                name="bad",
                type="file_siza",
                path="a",
                min_size_bytes=100,
                max_size_bytes=10,
            ),
            "min_size_bytes",
        ),
        (
            ArtifactValidationRule(
                name="bad",
                type="file_extension",
                path="a",
            ),
            "allowed_extensions",
        ),
        (
            ArtifactValidationRule(
                name="bad",
                type="csv_content",
                path="a",
            ),
            "csv_content requires",
        ),
        (
            ArtifactValidationRule(
                name="bad",
                type="json_content",
                path="a",
            ),
            "json_content requires",
        ),
    ],
)
def test_invalid_cross_fields(rule, fragment):
    """
    Given an artifact rule with the parameterized semantic violation.
    When cross-field validation runs.
    Then the matching constraint diagnostic is raised.
    """
    with pytest.raises(ConfigurationValidationError, match=fragment):
        validate_cross_fields(config_with_rules(rule))


def test_duplicate_rule_names_rejected():
    """
    Given two artifact rules sharing a name.
    When cross-field validation runs.
    Then duplicate artifact rule names are rejected.
    """
    rules = [
        ArtifactValidationRule(
            name="same",
            type="exists",
            path="a",
        ),
        ArtifactValidationRule(
            name="same",
            type="exists",
            path="a",
        ),
    ]

    with pytest.raises(ConfigurationValidationError, match="duplicate artifact rule name"):
        validate_cross_fields(config_with_rules(*rules))


def test_cleanup_after_step_rejected():
    """
    Given an artifact rule referencing a teardown step.
    When cross-field validation runs.
    Then cleanup attempt-level validation is rejected.
    """
    config = config_with_rules(
        ArtifactValidationRule(
            name="x",
            type="exists",
            path="x",
            after_step="clean",
        )
    )
    config = replace(
        config,
        lifecycle=replace(
            config.lifecycle,
            teardown=LifecycleSteps(
                [
                    LifecycleStepContent(
                        name="clean",
                        type="command",
                        command="echo clean",
                        timeout_second=10,
                    )
                ]
            ),
        ),
    )

    with pytest.raises(ConfigurationValidationError, match="cleanup step"):
        validate_cross_fields(config)


def test_valid_cross_field():
    """
    Given a CSV rule referencing an existing step with required columns.
    When cross-field validation runs.
    Then the semantic configuration is accepted.
    """
    validate_cross_fields(
        config_with_rules(
            ArtifactValidationRule(
                name="power_csv",
                type="csv_content",
                path="result.csv",
                after_step="power",
                required_columns=["voltage"],
            )
        )
    )


def test_loader_validates_schema_and_cross_fields(tmp_path):
    """
    Given a valid YAML file with a timeout template.
    When the loader reads it and then reads an unknown after_step mutation.
    Then the template is preserved and the mutation raises an unknown-step error.
    """
    raw = valid_raw()

    path = tmp_path / "scenario.yml"

    path.write_text(
        yaml.safe_dump(raw),
        encoding="utf-8",
    )

    config = ConfigLoader().load(str(path))

    assert config.lifecycle.scenario.steps[0].timeout_second == "${{vars.duration}}"

    raw["artifact"]["validation"]["rules"][0]["after_step"] = "missing"

    path.write_text(
        yaml.safe_dump(raw),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationValidationError, match="unknown step"):
        ConfigLoader().load(str(path))


@pytest.mark.parametrize("value", [None, [], "invalid", 42])
@pytest.mark.parametrize(
    "path",
    [
        (),
        ("test_case",),
        ("device",),
        ("variables",),
        ("lifecycle",),
        ("lifecycle", "scenario"),
        ("lifecycle", "scenario", "steps", 0),
        ("artifact",),
        ("artifact", "validation"),
        ("artifact", "validation", "rules", 0),
        ("retry",),
    ],
)
def test_non_mapping_values_report_validation_errors(path, value):
    """
    Given a non-mapping value at the parameterized configuration location.
    When schema validation runs.
    Then an expected-mapping diagnostic is raised.
    """
    raw = valid_raw()
    if not path:
        raw = value
    else:
        parent = raw
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = value

    with pytest.raises(ConfigurationValidationError, match="expected mapping"):
        validate_schema(raw)


@pytest.mark.parametrize("field", ["run_timeout_seconds", "cleanup_timeout_seconds"])
@pytest.mark.parametrize("value", [0, -1, False, "10", float("inf")])
def test_invalid_run_and_cleanup_timeouts(field, value):
    """
    Given the selected scope timeout contains the parameterized invalid value.
    When schema validation runs.
    Then the selected timeout diagnostic is raised.
    """
    raw = valid_raw()
    raw[field] = value
    with pytest.raises(ConfigurationValidationError, match=field):
        validate_schema(raw)
