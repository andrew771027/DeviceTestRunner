import math
import re

from runner.models import RunnerConfig

STAGES = (
    "global_setup",
    "setup",
    "scenario",
    "teardown",
    "global_teardown",
)
RULE_TYPES = {
    "exists",
    "file_size",
    "file_extension",
    "directory_not_empty",
    "csv_content",
    "json_content",
}
NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TEMPLATE = re.compile(r"^\$\{\{\s*[^{}]+\s*\}\}$")


class ConfigurationValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid runner configuration:\n" + "\n".join(f"- {e}" for e in errors))


def _mapping(value, path, errors):

    if not isinstance(value, dict):

        errors.append(f"{path}: expected mapping")
        return {}

    return value


def _keys(value, allowed, required, path, errors):
    for k in value:

        if k not in allowed:

            errors.append(f"{path}.{k}: unknown field")

    for k in required:

        if k not in value:

            errors.append(f"{path}.{k}: required field missing")


def _string(value, path, errors, *, template=True):
    if not isinstance(value, str) or not value.strip():

        errors.append(f"{path}: expected non-empty string")

    elif not template and "${{" in value:

        errors.append(f"{path}: template not supported")


def _number(value, path, errors, *, minimum=0, integer=False, allow_template=False):
    if allow_template and isinstance(value, str) and TEMPLATE.fullmatch(value):
        return

    valid = type(value) is int if integer else type(value) in (int, float)

    if not valid or not math.isfinite(value) or value < minimum:

        errors.append(f"{path}: expected {'integer' if integer else 'number'} >= {minimum}")


def validate_schema(raw: dict) -> None:
    """Validate YAML shape before constructing dataclasses; collect all errors."""
    errors = []

    raw = _mapping(
        value=raw,
        path="root",
        errors=errors,
    )

    _keys(
        value=raw,
        allowed={
            "test_case",
            "device",
            "variables",
            "lifecycle",
            "artifact",
            "retry",
            "run_timeout_seconds",
            "cleanup_timeout_seconds",
        },
        required={
            "test_case",
            "device",
            "lifecycle",
            "artifact",
        },
        path="root",
        errors=errors,
    )

    for section, required in (
        ("test_case", ("id", "name", "description")),
        ("device", ("serial", "product", "build")),
    ):

        obj = _mapping(
            value=raw.get(section),
            path=section,
            errors=errors,
        )

        _keys(
            value=obj,
            allowed=set(required),
            required=required,
            path=section,
            errors=errors,
        )

        for field in required:

            if field in obj:

                _string(
                    value=obj[field],
                    path=f"{section}.{field}",
                    errors=errors,
                )

    variables = _mapping(
        value=raw.get("variables", {}),
        path="variables",
        errors=errors,
    )

    for key, value in variables.items():

        if not isinstance(key, str) or not NAME.fullmatch(key):

            errors.append(f"variables.{key}: invalid variable name")

        if type(value) not in (str, int, float, bool) or (
            type(value) is float and not math.isfinite(value)
        ):

            errors.append(f"variables.{key}: expected finite scalar")

    lifecycle = _mapping(
        value=raw.get("lifecycle"),
        path="lifecycle",
        errors=errors,
    )

    _keys(
        value=lifecycle,
        allowed=set(STAGES),
        required=set(),
        path="lifecycle",
        errors=errors,
    )

    for stage in STAGES:

        obj = _mapping(
            value=lifecycle.get(stage, {"steps": []}),
            path=f"lifecycle.{stage}",
            errors=errors,
        )

        _keys(
            value=obj,
            allowed={"steps"},
            required={"steps"},
            path=f"lifecycle.{stage}",
            errors=errors,
        )

        steps = obj.get("steps", [])

        if not isinstance(steps, list):

            errors.append(f"lifecycle.{stage}.steps: expected list")

            continue

        for i, step in enumerate(steps):

            path = f"lifecycle.{stage}.steps[{i}]"

            step = _mapping(value=step, path=path, errors=errors)

            _keys(
                value=step,
                allowed={"name", "type", "command", "timeout_second"},
                required={"name", "type", "command"},
                path=path,
                errors=errors,
            )

            for key in ("name", "type", "command"):

                if key in step:

                    _string(
                        value=step[key],
                        path=f"{path}.{key}",
                        errors=errors,
                    )

            if "timeout_second" in step:

                _number(
                    value=step["timeout_second"],
                    path=f"{path}.timeout_second",
                    errors=errors,
                    minimum=1,
                    integer=True,
                    allow_template=True,
                )

    artifact = _mapping(
        value=raw.get("artifact"),
        path="artifact",
        errors=errors,
    )

    _keys(
        value=artifact,
        allowed={"output_dir", "validation"},
        required={"output_dir"},
        path="artifact",
        errors=errors,
    )

    if "output_dir" in artifact:

        _string(
            value=artifact["output_dir"],
            path="artifact.output_dir",
            errors=errors,
        )

    validation = _mapping(
        value=artifact.get("validation", {}),
        path="artifact.validation",
        errors=errors,
    )

    _keys(
        value=validation,
        allowed={"rules"},
        required=set(),
        path="artifact.validation",
        errors=errors,
    )

    rules = validation.get("rules", [])

    if not isinstance(rules, list):

        errors.append("artifact.validation.rules: expected list")

        rules = []

    rule_fields = (
        "name",
        "type",
        "path",
        "after_step",
        "required",
        "min_size_bytes",
        "max_size_bytes",
        "allowed_extensions",
        "required_columns",
        "min_rows",
        "required_json_paths",
        "expected_json_values",
    )

    for i, rule in enumerate(rules):

        path = f"artifact.validation.rules[{i}]"

        rule = _mapping(
            value=rule,
            path=path,
            errors=errors,
        )

        _keys(
            value=rule,
            allowed=rule_fields,
            required={"name", "type", "path"},
            path=path,
            errors=errors,
        )

        for key in ("name", "type", "path"):

            if key in rule:

                _string(
                    value=rule[key],
                    path=f"{path}.{key}",
                    errors=errors,
                )

        if "after_step" in rule and rule["after_step"] is not None:

            _string(
                value=rule["after_step"],
                path=f"{path}.after_step",
                errors=errors,
                template=False,
            )

        if "required" in rule and type(rule["required"]) is not bool:

            errors.append(f"{path}.required: expected boolean")

        for key in ("min_size_bytes", "max_size_bytes", "min_rows"):

            if key in rule and rule[key] is not None:

                _number(
                    value=rule[key],
                    path=f"{path}.{key}",
                    errors=errors,
                    minimum=0,
                    integer=True,
                )

        for key in (
            "allowed_extensions",
            "required_columns",
            "required_json_paths",
        ):

            if key in rule and (
                not isinstance(rule[key], list)
                or any(not isinstance(v, str) or not v for v in rule[key])
            ):

                errors.append(f"{path}.{key}: expected list of non-empty strings")

        if "expected_json_values" in rule and not isinstance(rule["expected_json_values"], dict):

            errors.append(f"{path}.expected_json_values: expected mapping")

    retry = _mapping(
        value=raw.get("retry", {}),
        path="retry",
        errors=errors,
    )

    _keys(
        value=retry,
        allowed={"max_attempts", "delay_seconds", "retry_on"},
        required=set(),
        path="retry",
        errors=errors,
    )

    if "max_attempts" in retry:

        _number(
            value=retry["max_attempts"],
            path="retry.max_attempts",
            errors=errors,
            minimum=1,
            integer=True,
        )

    if "delay_seconds" in retry:

        _number(
            value=retry["delay_seconds"],
            path="retry.delay_seconds",
            errors=errors,
            minimum=0,
        )

    if "retry_on" in retry and (
        not isinstance(retry["retry_on"], list)
        or any(not isinstance(x, str) for x in retry["retry_on"])
    ):

        errors.append("retry.retry_on: expected list of strings")

    for field in ("run_timeout_seconds", "cleanup_timeout_seconds"):

        if field in raw and raw[field] is not None:

            _number(
                value=raw[field],
                path=field,
                errors=errors,
                minimum=0.00000001,
            )

    if errors:

        raise ConfigurationValidationError(errors)


def validate_cross_fields(config: RunnerConfig) -> None:
    """Validate semantic relations independent of variable expansion."""
    errors = []

    all_steps = [
        (stage, step) for stage in STAGES for step in getattr(config.lifecycle, stage).steps
    ]

    names = {}

    for stage, step in all_steps:

        if step.name in names:

            errors.append(
                f"lifecycle.{stage}: duplicate step name {step.name!r} "
                f"(first in {names[step.name]})"
            )

        else:

            names[step.name] = stage

        if step.type != "command":

            errors.append(f"lifecycle.{stage}.{step.name}: unsupported step type {step.type!r}")

    seen_rules = set()

    for rule in config.artifact.validation.rules:

        path = f"artifact.validation.{rule.name}"

        if rule.name in seen_rules:

            errors.append(f"{path}: duplicate artifact rule name")

        seen_rules.add(rule.name)

        if rule.type not in RULE_TYPES:

            errors.append(f"{path}: unsupported validation type {rule.type!r}")

        if rule.after_step is not None and rule.after_step not in names:

            errors.append(f"{path}: after_step: unknown step {rule.after_step!r}")

        if rule.after_step is not None and names.get(rule.after_step) in (
            "teardown",
            "global_teardown",
        ):

            errors.append(
                f"{path}.after_step: cleanup step cannot use attempt-level artifact validation"
            )

        if (
            rule.min_size_bytes is not None
            and rule.max_size_bytes is not None
            and rule.min_size_bytes > rule.max_size_bytes
        ):

            errors.append(f"{path}: min_size_bytes exceeds max_size_bytes")

        if rule.type == "file_extension" and not rule.allowed_extensions:

            errors.append(f"{path}: file_extension requires allowed_extensions")

        if rule.type == "csv_content" and rule.min_rows is None and not rule.required_columns:

            errors.append(f"{path}: csv_content requires min_rows or required_columns")

        if (
            rule.type == "json_content"
            and not rule.required_json_paths
            and not rule.expected_json_values
        ):

            errors.append(f"{path}: json_content requires JSON constraints")

    if errors:

        raise ConfigurationValidationError(errors)
