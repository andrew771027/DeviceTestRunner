import pytest

from runner.models import ArtifactValidationRule, DeviceInfo, LifecycleStepContent
from runner.variables import StaticVariableResolver, VariableResolutionError


def test_device_context_in_command_and_artifact(tmp_path):
    resolver = StaticVariableResolver(
        {"output_name": "result.csv"}, tmp_path, environ={"DEVICE_SERIAL": "pixel-007"}
    )
    unresolved = DeviceInfo(
        serial="${{ env.DEVICE_SERIAL }}",
        product="pixel",
        build="build-123",
    )
    device = resolver.resolve_dataclass(unresolved, path="device")
    resolver.bind_device(device)
    step = LifecycleStepContent(
        name="test",
        type="command",
        command="python run.py --serial ${{ device.serial }} --product ${{ device.product }}",
        timeout_second=600,
    )
    resolved = resolver.resolve_dataclass(step, path="lifecycle.scenario.steps[0]")

    assert resolved.command == "python run.py --serial pixel-007 --product pixel"
    assert step.command.endswith("${{ device.product }}")
    rule = ArtifactValidationRule(
        name="output",
        type="exists",
        path="${{ run.dir }}/${{ vars.output_name }}",
    )
    assert resolver.resolve_dataclass(rule).path == str(tmp_path / "result.csv")


def test_context_is_not_bound_early():
    resolver = StaticVariableResolver({}, ".")
    with pytest.raises(VariableResolutionError, match="not bound"):
        resolver.string("${{ device.serial }}", "command")


def test_unknown_device_field():
    resolver = StaticVariableResolver({}, ".")
    resolver.bind_device(
        DeviceInfo(
            serial="serial",
            product="pixel",
            build="build",
        )
    )
    with pytest.raises(VariableResolutionError, match="unsupported device context"):
        resolver.string("${{ device.imei }}", "command")


def test_context_cannot_be_rebound():
    resolver = StaticVariableResolver({}, ".")
    device = DeviceInfo(
        serial="serial",
        product="pixel",
        build="build",
    )
    resolver.bind_device(device)
    with pytest.raises(VariableResolutionError, match="already bound"):
        resolver.bind_device(device)


@pytest.mark.parametrize("bad", ["", "${{ device.serial }}", "${{ env.MISSING }}"])
def test_unresolved_device_metadata_is_rejected(bad):
    resolver = StaticVariableResolver({}, ".")
    with pytest.raises(VariableResolutionError, match="resolved non-empty"):
        resolver.bind_device(
            DeviceInfo(
                serial=bad,
                product="pixel",
                build="build",
            )
        )


def test_device_metadata_from_env_is_snapshotted(monkeypatch):
    monkeypatch.setenv("DEVICE_SERIAL", "before")
    resolver = StaticVariableResolver({}, ".")
    monkeypatch.setenv("DEVICE_SERIAL", "after")
    device = resolver.resolve_dataclass(
        DeviceInfo(
            serial="${{ env.DEVICE_SERIAL }}",
            product="pixel",
            build="build",
        )
    )
    resolver.bind_device(device)
    assert resolver.string("${{ device.serial }}", "command") == "before"
