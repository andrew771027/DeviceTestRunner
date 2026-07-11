import yaml


def test_config_yaml_contract(tmp_path):
    config_file = tmp_path / "contract.yaml"
    config_file.write_text(
        """
test_case:
  id: power_002
  name: Contract Test
  description: This is contract test
device:
  serial: xxxx_002
  product: pixel_002
  build: test_build_002
workflow:
  steps:
    - name: setup
      type: command
      command: "echo Hello World"
      timeout_second: 10
    - name: run
      type: command
      command: "echo Hello Python"
      timeout_second: 10
artifact:
  output_dir: "runs/contract_test"
""",
        encoding="utf-8",
    )

    data = yaml.safe_load(config_file.read_text(encoding="utf-8"))

    assert isinstance(data, dict)

    assert "test_case" in data
    assert isinstance(data["test_case"], dict)

    assert "workflow" in data
    assert isinstance(data["workflow"], dict)

    assert "artifact" in data
    assert isinstance(data["artifact"], dict)

    assert "steps" in data["workflow"]
    assert isinstance(data["workflow"]["steps"], list)

    for step in data["workflow"]["steps"]:
        assert isinstance(step, dict)

        assert "name" in step
        assert isinstance(step["name"], str)

        assert "type" in step
        assert isinstance(step["type"], str)

        assert "command" in step
        assert isinstance(step["command"], str)

        assert "timeout_second" in step
        assert isinstance(step["timeout_second"], int)
