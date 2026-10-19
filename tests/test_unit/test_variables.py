from dataclasses import dataclass, field

import pytest

from runner.variables import StaticVariableResolver, VariableResolutionError


@pytest.fixture
def resolver(tmp_path):
    return StaticVariableResolver(
        {
            "repeat": 3,
            "test_duration": 600,
            "output_name": "power_result.csv",
        },
        tmp_path,
    )


def test_command_interpolation(resolver):
    """
    Given a repeat variable with integer value 3.
    When the command embeds the repeat placeholder.
    Then the command contains the string argument 3.
    """
    command = resolver.string("python run.py --repeat ${{ vars.repeat }}", "command")
    assert command == "python run.py --repeat 3"


def test_timeout_preserves_integer(resolver):
    """
    Given an integer test_duration variable.
    When timeout resolves a whole variable reference.
    Then the result is integer 600 and retains its int type.
    """
    assert resolver.timeout("${{ vars.test_duration }}") == 600
    assert type(resolver.timeout("${{ vars.test_duration }}")) is int


@pytest.mark.parametrize("value", [1, 0.1, 3.5])
def test_timeout_accepts_positive_numbers(tmp_path, value):
    """
    Given a positive integer or float duration.
    When timeout receives the literal and its whole variable reference.
    Then both results retain the value and exact numeric type.
    """
    resolver = StaticVariableResolver({"duration": value}, tmp_path)
    for timeout in (value, "${{ vars.duration }}"):
        result = resolver.timeout(timeout)
        assert result == value
        assert type(result) is type(value)


def test_artifact_path(resolver, tmp_path):
    """
    Given a run directory and output filename variable.
    When the path combines run.dir and the filename.
    Then the result matches the absolute file path.
    """
    assert resolver.string("${{ run.dir }}/${{ vars.output_name }}", "path") == str(
        tmp_path.resolve() / "power_result.csv"
    )


def test_multiple_references(resolver):
    """
    Given a repeat variable with value 3.
    When a string references it twice.
    Then both placeholders resolve to produce 3-3.
    """
    assert resolver.string("${{ vars.repeat }}-${{ vars.repeat }}", "command") == "3-3"


@pytest.mark.parametrize(
    "expression",
    [
        "${{ vars.missing }}",
        "${{ env.SECRET }}",
        "${{ vars.repeat * 2 }}",
        "${{ vars.repeat }",
    ],
)
def test_unknown_or_malformed_expression_fails(resolver, expression):
    """
    Given an undefined, unsupported or malformed expression.
    When resolve processes the expression.
    Then VariableResolutionError is raised.
    """
    with pytest.raises(VariableResolutionError):
        resolver.resolve(expression)


@pytest.mark.parametrize(
    "variables",
    [
        {"x": [1, 2]},
        {"x": {"y": 1}},
        {"bad-name": 1},
        {"x": "${{ vars.y }}"},
    ],
)
def test_invalid_variable_definitions(tmp_path, variables):
    """
    Given an unsupported value, invalid name or recursive reference.
    When the resolver validates the variable definitions.
    Then VariableResolutionError is raised.
    """
    with pytest.raises(VariableResolutionError):
        StaticVariableResolver(variables, tmp_path)


@pytest.mark.parametrize(
    "value",
    [
        "${{ vars.repeat }}s",
        0,
        -1,
        True,
        False,
        0.0,
        -0.1,
        float("nan"),
        float("inf"),
        float("-inf"),
        None,
        "600",
    ],
)
def test_invalid_timeout_values(tmp_path, value):
    """
    Given a nonpositive, nonfinite, boolean or nonnumeric timeout.
    When timeout validates the supplied value.
    Then VariableResolutionError is raised.
    """
    resolver = StaticVariableResolver({"repeat": 3}, tmp_path)
    with pytest.raises(VariableResolutionError):
        resolver.timeout(value)


def test_missing_value_fails_as_string(resolver):
    """
    Given a whole reference to the integer repeat variable.
    When string validates it as a command.
    Then VariableResolutionError rejects the non-string result.
    """
    with pytest.raises(VariableResolutionError):
        resolver.string("${{ vars.repeat }}", "command")


def test_unsupported_nested_tempalte(tmp_path):
    """
    Given a variable value containing a run.dir template.
    When the resolver validates its definitions.
    Then VariableResolutionError rejects the recursive template.
    """
    with pytest.raises(VariableResolutionError):
        StaticVariableResolver({"name": "${{ run.dir }}"}, tmp_path)


@dataclass(frozen=True)
class LifecycleStepContent:
    name: str
    type: str
    command: str
    timeout_second: int | float | str


@dataclass(frozen=True)
class LifecycleSteps:
    steps: list[LifecycleStepContent] = field(default_factory=list)


@dataclass(frozen=True)
class LifecycleConfig:
    scenario: LifecycleSteps = field(default_factory=LifecycleSteps)


@dataclass(frozen=True)
class ArtifactValidationRule:
    name: str
    path: str


@dataclass(frozen=True)
class ArtifactValidationConfig:
    rules: list[ArtifactValidationRule] = field(default_factory=list)


def test_resolve_models_without_mutating_original(resolver):
    """
    Given a frozen lifecycle with command and timeout templates.
    When resolve_dataclass creates a resolved lifecycle.
    Then the copy resolves both fields and the original command remains unchanged.
    """
    original = LifecycleConfig(
        LifecycleSteps(
            [
                LifecycleStepContent(
                    "run",
                    "command",
                    "echo ${{ vars.repeat }}",
                    "${{ vars.test_duration }}",
                ),
            ],
        ),
    )
    result = resolver.resolve_dataclass(original)
    assert result.scenario.steps[0].command == "echo 3"
    assert result.scenario.steps[0].timeout_second == 600
    assert original.scenario.steps[0].command == "echo ${{ vars.repeat }}"


def test_resolve_artifact_rules(resolver, tmp_path):
    """
    Given an artifact rule using run.dir and an output variable.
    When resolve_dataclass resolves the validation configuration.
    Then the rule path matches the absolute output path.
    """
    original = ArtifactValidationConfig(
        [ArtifactValidationRule("power", "${{ run.dir }}/${{ vars.output_name }}")]
    )
    result = resolver.resolve_dataclass(original)
    assert result.rules[0].path == str(tmp_path.resolve() / "power_result.csv")
