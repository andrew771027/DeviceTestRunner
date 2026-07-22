import yaml


def test_config_yaml_contract(tmp_path):
    config_file = tmp_path / "contract.yaml"
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

    lifecycle:
        global_setup:
            steps:
            - name: Hello World 1
              type: command
              command: "echo 'Hello World 1'"
              timeout_second: 1
        setup:
            steps:
            - name: Hello World 2
              type: command
              command: "echo 'Hello World 2'"
              timeout_second: 1
        scenario:
            steps:
            - name: Hello World 3
              type: command
              command: "echo 'Hello World 3'"
              timeout_second: 1
            - name: Hello World 4
              type: command
              command: "echo 'Hello World 4'"
              timeout_second: 1
        teardown:
            steps:
            - name: Hello World 5
              type: command
              command: "echo 'Hello World 5'"
              timeout_second: 1
        global_teardown:
            steps:
            - name: Hello World 6
              type: command
              command: "echo 'Hello World 6'"
              timeout_second: 1
    artifact:
        output_dir: artufact/hello_world
""",
        encoding="utf-8",
    )

    data = yaml.safe_load(config_file.read_text(encoding="utf-8"))

    assert isinstance(data, dict)

    assert "test_case" in data
    assert isinstance(data["test_case"], dict)

    assert "device" in data
    assert isinstance(data["device"], dict)

    assert "lifecycle" in data
    assert isinstance(data["lifecycle"], dict)

    assert "artifact" in data
    assert isinstance(data["artifact"], dict)

    assert "global_setup" in data["lifecycle"]
    assert isinstance(data["lifecycle"]["global_setup"]["steps"], list)

    assert "setup" in data["lifecycle"]
    assert isinstance(data["lifecycle"]["setup"]["steps"], list)

    assert "scenario" in data["lifecycle"]
    assert isinstance(data["lifecycle"]["scenario"]["steps"], list)

    assert "teardown" in data["lifecycle"]
    assert isinstance(data["lifecycle"]["teardown"]["steps"], list)

    assert "global_teardown" in data["lifecycle"]
    assert isinstance(data["lifecycle"]["global_teardown"]["steps"], list)

    for step in data["lifecycle"]["global_setup"]["steps"]:
        assert isinstance(step, dict)

        assert "name" in step
        assert isinstance(step["name"], str)

        assert "type" in step
        assert isinstance(step["type"], str)

        assert "command" in step
        assert isinstance(step["command"], str)

        assert "timeout_second" in step
        assert isinstance(step["timeout_second"], int)
