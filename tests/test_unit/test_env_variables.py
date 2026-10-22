import os
from dataclasses import replace
from pathlib import Path

import pytest

from runner.models import DeviceInfo
from runner.variables import StaticVariableResolver, VariableResolutionError

def test_env_device_serial(monkeypatch):
    monkeypatch.setenv("DEVICE_SERIAL", "pixel-123")
    
    resolver = StaticVariableResolver({}, ".")
    device = DeviceInfo(serial="${{ env.DEVICE_SERIAL }}", product="pixel", build="build",)
    resolved = resolver.resolve_dataclass(device, path="device",)
    
    assert resolved.serial == "pixel-123"
    assert device.serial == "${{ env.DEVICE_SERIAL }}"

def test_env_command_and_path(monkeypatch, tmp_path):
    monkeypatch.setenv("DEVICE_SERIAL", "abc-123")
    
    resolver = StaticVariableResolver({"repeat": 3}, tmp_path)
    
    assert resolver.string("adb -s ${{ env.DEVICE_SERIAL }} shell echo ${{ vars.repeat }}", "command") == "adb -s abc-123 shell echo 3"
    assert resolver.string("${{ run.dir }}/out.csv", "path") == str(tmp_path / "out.csv")

def test_missing_env_is_fail_fast(monkeypatch):
    monkeypatch.delenv("DEVICE_SERIAL", raising=False)
    resolver = StaticVariableResolver({}, ".")

    with pytest.raises(VariableResolutionError, match="undefined environment variable"):
        resolver.string("${{ env.DEVICE_SERIAL }}", "device.serial")

@pytest.mark.parametrize(
    "expression",
    [
        "${{ env }}",
        "${{ env.A-B }}",
        "${{ env.HOME.lower() }}"
    ]
)
def test_invalid_env_expression(expression):
    resolver = StaticVariableResolver({}, ".")

    with pytest.raises(VariableResolutionError):
        resolver.string(expression, "device.serial")

def test_empty_environment_variable_is_defined():
    resolver = StaticVariableResolver({}, ".", environ={"DEVICE_SERIAL": ""},)

    assert resolver.string("${{ env.DEVICE_SERIAL }}", "device.serial") == ""

def test_environment_is_snapshpt(monkeypatch):
    monkeypatch.setenv("DEVICE_SERIAL", "before")

    resolver = StaticVariableResolver({}, ".")

    monkeypatch.setenv("DEVICE_SERIAL", "after")

    assert resolver.string("${{ env.DEVICE_SERIAL }}", "device.serial") == "before"

def test_env_does_not_change_numeric_timeout():
    resolver = StaticVariableResolver({}, ".", environ={"DURATION": "600"})

    with pytest.raises(VariableResolutionError, match="positive number"):
        resolver.timeout("${{ env.DURATION }}")