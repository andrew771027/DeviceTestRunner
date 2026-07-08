import yaml

from runner.models import ArtifactConfig, ScenarioConfig, TestConfig


class ConfigLoader:

    def load(self, path: str) -> TestConfig:
        with open(path, "r") as f:
            raw = yaml.safe_load(f)

        return TestConfig(
            test_name=raw["test_name"],
            scenario=ScenarioConfig(
                command=raw["scenario"]["command"],
                timeout_second=raw["scenario"]["timeout_second"],
            ),
            artifact=ArtifactConfig(output_dir=raw["artifact"]["output_dir"]),
        )
