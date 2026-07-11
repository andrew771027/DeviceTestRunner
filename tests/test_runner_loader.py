from runner.config import ConfigLoader
from runner.models import RunnerConfig


def test_runner_loader_loads_steps_yaml(tmp_path):
    config_file = tmp_path / "sample.yaml"
    config_file.write_text(
        """
    test_case:
        id: hello_world_001
        name: hello_world
        description: this is hello world.
    device:
        serial: xxx001
        product: pixel
        build: 2026.xx.001

    workflow:
        steps:
            - name: Hello World 1
              type: command
              command: "echo Hello World 1"
              timeout_second: 1
            - name: Hello World 2
              type: command
              command: "echo Hello World 2"
              timeout_second: 2
    artifact:
        output_dir: artufact/hello_world
""",
        encoding="utf-8",
    )

    config = ConfigLoader().load(str(config_file))

    assert isinstance(config, RunnerConfig)
    assert config.test_case.name == "hello_world"

    assert len(config.workflow.steps) == 2

    assert config.workflow.steps[0].name == "Hello World 1"
    assert config.workflow.steps[0].command == "echo Hello World 1"

    assert config.workflow.steps[1].name == "Hello World 2"
    assert config.workflow.steps[1].command == "echo Hello World 2"

    assert config.artifact.output_dir == "artufact/hello_world"
