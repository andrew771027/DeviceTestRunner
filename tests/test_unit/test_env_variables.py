import pytest

from runner.models import DeviceInfo
from runner.variables import StaticVariableResolver, VariableResolutionError


def test_env_device_serial(monkeypatch):
    """
    Given a host DEVICE_SERIAL and unresolved DeviceInfo.
    When the resolver copies device fields.
    Then the serial resolves and the original template remains unchanged.
    """
    monkeypatch.setenv("DEVICE_SERIAL", "pixel-123")

    resolver = StaticVariableResolver({}, ".")
    device = DeviceInfo(
        serial="${{ env.DEVICE_SERIAL }}",
        product="pixel",
        build="build",
    )
    resolved = resolver.resolve_dataclass(
        device,
        path="device",
    )

    assert resolved.serial == "pixel-123"
    assert device.serial == "${{ env.DEVICE_SERIAL }}"


def test_env_command_and_path(monkeypatch, tmp_path):
    """
    Given host serial, typed repeat and a temporary run directory.
    When command and path strings are resolved.
    Then command interpolation and the absolute artifact path match.
    """
    monkeypatch.setenv("DEVICE_SERIAL", "abc-123")

    resolver = StaticVariableResolver({"repeat": 3}, tmp_path)

    command = resolver.string(
        "adb -s ${{ env.DEVICE_SERIAL }} shell echo ${{ vars.repeat }}", "command"
    )
    assert command == "adb -s abc-123 shell echo 3"
    assert resolver.string("${{ run.dir }}/out.csv", "path") == str(tmp_path / "out.csv")


def test_missing_env_is_fail_fast(monkeypatch):
    """
    Given DEVICE_SERIAL is absent from the host.
    When a device.serial env reference is resolved.
    Then VariableResolutionError identifies an undefined environment variable.
    """
    monkeypatch.delenv("DEVICE_SERIAL", raising=False)
    resolver = StaticVariableResolver({}, ".")

    with pytest.raises(VariableResolutionError, match="undefined environment variable"):
        resolver.string("${{ env.DEVICE_SERIAL }}", "device.serial")


@pytest.mark.parametrize("expression", ["${{ env }}", "${{ env.A-B }}", "${{ env.HOME.lower() }}"])
def test_invalid_env_expression(expression):
    """
    Given an unsupported or malformed env expression.
    When the expression is resolved as a string.
    Then VariableResolutionError is raised.
    """
    resolver = StaticVariableResolver({}, ".")

    with pytest.raises(VariableResolutionError):
        resolver.string(expression, "device.serial")


def test_empty_environment_variable_is_defined():
    """
    Given an explicit environment mapping contains an empty serial.
    When the serial reference is resolved.
    Then the empty string is returned without a missing-variable error.
    """
    resolver = StaticVariableResolver(
        {},
        ".",
        environ={"DEVICE_SERIAL": ""},
    )

    assert resolver.string("${{ env.DEVICE_SERIAL }}", "device.serial") == ""


def test_environment_is_snapshpt(monkeypatch):
    """
    Given a resolver captures DEVICE_SERIAL before a host change.
    When the host value changes and the existing resolver reads the reference.
    Then the captured value remains before.
    """
    monkeypatch.setenv("DEVICE_SERIAL", "before")

    resolver = StaticVariableResolver({}, ".")

    monkeypatch.setenv("DEVICE_SERIAL", "after")

    assert resolver.string("${{ env.DEVICE_SERIAL }}", "device.serial") == "before"


def test_env_does_not_change_numeric_timeout():
    """
    Given DURATION is the environment string 600.
    When the env reference is resolved as a timeout.
    Then the numeric string is rejected as a nonnumeric timeout.
    """
    resolver = StaticVariableResolver({}, ".", environ={"DURATION": "600"})

    with pytest.raises(VariableResolutionError, match="positive number"):
        resolver.timeout("${{ env.DURATION }}")
