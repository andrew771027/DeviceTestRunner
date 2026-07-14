import yaml

from runner.models import (
    ArtifactConfig,
    DeviceInfo,
    DeviceTestCase,
    RunnerConfig,
    Workflow,
    WorkflowStep,
)


class ConfigLoader:

    def load(self, path: str) -> RunnerConfig:
        with open(path, "r") as f:
            raw = yaml.safe_load(f)

        test_case = DeviceTestCase(
            id=raw["test_case"]["id"],
            name=raw["test_case"]["name"],
            description=raw["test_case"]["description"],
        )

        device = DeviceInfo(
            serial=raw["device"]["serial"],
            product=raw["device"]["serial"],
            build=raw["device"]["build"],
        )

        steps = [
            WorkflowStep(
                name=item["name"],
                type=item["type"],
                command=item["command"],
                timeout_second=item.get("timeout_second", 60),
            )
            for item in raw["workflow"]["steps"]
        ]

        workflow = Workflow(steps=steps)

        artifact = ArtifactConfig(output_dir=raw["artifact"]["output_dir"])

        return RunnerConfig(
            test_case=test_case,
            device=device,
            workflow=workflow,
            artifact=artifact,
        )
