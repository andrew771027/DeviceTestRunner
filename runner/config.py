from typing import Any

import yaml

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



class ConfigLoader:

    DEFAULT_RETRY_ON = [
        FailureType.TIMEOUT,
        FailureType.DEVICE_OFFLINE,
        FailureType.PROCESS_ERROR,
        FailureType.ARTIFACT_MISSING,
        FailureType.ARTIFACT_INVALID,
    ]

    def load(self, path: str) -> RunnerConfig:
        with open(path, "r") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise ValueError("Config root must be a YAML mapping.")

        test_case = self._load_test_case(raw)

        device = self._load_device(raw)

        lifecycle_raw = raw.get("lifecycle", {})

        lifecycle = LifecycleConfig(
            global_setup=self._load_steps(lifecycle_raw.get("global_setup", {})),
            setup=self._load_steps(lifecycle_raw.get("setup", {})),
            scenario=self._load_steps(lifecycle_raw.get("scenario", {})),
            teardown=self._load_steps(lifecycle_raw.get("teardown", {})),
            global_teardown=self._load_steps(lifecycle_raw.get("global_teardown", {})),
        )

        artifact = ArtifactConfig(
            output_dir=raw["artifact"]["output_dir"],
            validation=self._load_validation(raw["artifact"]),
        )

        retry = self._load_retry(raw)

        return RunnerConfig(
            test_case=test_case,
            device=device,
            lifecycle=lifecycle,
            retry=retry,
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

        return DeviceInfo(
            serial=device["serial"], product=device["product"], build=device["build"]
        )

    @staticmethod
    def _load_steps(raw: dict[str, Any]) -> LifecycleSteps:

        steps = raw["steps"]

        return LifecycleSteps(
            steps=[
                LifecycleStepContent(
                    name=step["name"],
                    type=step["type"],
                    command=step["command"],
                    timeout_second=step.get("timeout_second", 60),
                )
                for step in steps
            ]
        )

    @staticmethod
    def _load_validation(raw: dict[str, dict]) -> ArtifactValidationConfig:
        validation = raw.get("validation", {})

        return ArtifactValidationConfig(
            rules=[
                ArtifactValidationRule(
                    name=rule["name"],
                    type=rule["type"],
                    path=rule["path"],
                    after_step=rule.get("after_step"),
                    retry_on_failure=rule.get("retry_on_failure", False),
                    min_size_bytes=rule.get("min_size_bytes"),
                    max_size_bytes=rule.get("max_size_bytes"),
                    allowed_extensions=rule.get("allowed_extensions", []),
                    required_columns=list(rule.get("required_columns", [])),
                    min_rows=rule.get("min_rows"),
                    required_json_paths=list(rule.get("required_json_paths", [])),
                    expected_json_values=dict(rule.get("expected_json_values", {})),
                )
                for rule in validation.get("rules", [])
            ]
        )

    @staticmethod
    def _load_retry(raw: dict[str, dict]) -> RetryConfig:
        retry = raw.get("retry", {})

        max_attempts = retry.get("max_attempts", 1)
        delay_seconds = retry.get("delay_seconds", 0.0)

        if max_attempts < 1:
            raise ValueError("retry.max_attempts must be >= 1")

        if delay_seconds < 0:
            raise ValueError("retry.delay_seconds must be >= 0")

        raw_retry_on = retry.get("retry_on")

        if retry_on is None:
            retry_on = list(self.DEFAULT_RETRY_ON)
        else:
            retry_on = self._parse_retry_on(raw_retry_on)

        return RetryConfig(max_attempts=max_attempts, 
                           delay_seconds=delay_seconds, 
                           retry_on=retry_on)

    @staticmethod
    def _parse_retry_on(values: list[str]) -> list[FailureType]:

        retry_on: list[FailureType] = []

        for value in values:
            try:
                failure_type = FailureType(value)
            except ValueError:
                raise ValueError(f"Unknown retry failure type: {value}")
            
            if failure_type == FailureType.NONE:
                raise ValueError("retry_on cannnot contain 'none'")
            
            retry_on.append(failure_type)
        
        return retry_on