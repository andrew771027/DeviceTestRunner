from typing import Any, List

import yaml

from runner.models import (
    ArtifactConfig,
    DeviceInfo,
    DeviceTestCase,
    LifecycleConfig,
    LifecycleStep,
    RunnerConfig,
)


class ConfigLoader:

    def load(self, path: str) -> RunnerConfig:
        with open(path, "r") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise ValueError("Config root must be a YAML mapping.")

        test_case = self._load_test_case(raw)

        device = self._load_device(raw)

        lifecycle_raw = raw.get("lifecycle", {})

        lifecycle = LifecycleConfig(
            global_setup=self._load_steps(lifecycle_raw.get("global_setup", [])),
            setup=self._load_steps(lifecycle_raw.get("setup", [])),
            scenario=self._load_steps(lifecycle_raw.get("scenario", [])),
            teardown=self._load_steps(lifecycle_raw.get("teardown", [])),
            global_teardown=self._load_steps(lifecycle_raw.get("global_teardown", [])),
        )

        artifact = self._load_artifact(raw)

        artifact = ArtifactConfig(output_dir=raw["artifact"]["output_dir"])

        return RunnerConfig(
            test_case=test_case,
            device=device,
            lifecycle=lifecycle,
            artifact=artifact,
        )

    @staticmethod
    def _load_test_case(raw: dict[str, Any]) -> DeviceTestCase:

        test_case = raw["test_case"]

        return DeviceTestCase(
            id=test_case["id"],
            name=test_case["name"],
            description=test_case["description"],
        )

    @staticmethod
    def _load_device(raw: dict[str, Any]) -> DeviceInfo:

        device = raw["device"]

        return DeviceInfo(serial=device["serial"], product=device["product"], build=device["build"])

    @staticmethod
    def _load_steps(raw: List[dict[str, Any]]) -> LifecycleStep:

        steps = raw["steps"]

        return [
            LifecycleStep(
                name=step["name"],
                type=step["type"],
                command=step["command"],
                timeout_second=step.get("timeout_second", 60),
            )
            for step in steps
        ]

    @staticmethod
    def _load_artifact(raw: dict[str, dict]) -> ArtifactConfig:
        artifact = raw["artifact"]

        return ArtifactConfig(output_dir=artifact["output_dir"])
