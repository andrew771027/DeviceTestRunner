from runner.config import ConfigLoader
from runner.models import TestConfig


def test_config_loader_loads_yaml(tmp_path):
    config_file = tmp_path / "sample.yaml"
    config_file.write_text(
        """
    test_name: smoke_test

    scenario:
        command: "echo Hello World"
        timeout_second: 30

    artifact:
        output_dir: ./
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(str(config_file))

    assert isinstance(config, TestConfig)
    assert config.test_name == "smoke_test"
    assert config.scenario.command == "echo Hello World"
    assert config.artifact.output_dir == "./"
