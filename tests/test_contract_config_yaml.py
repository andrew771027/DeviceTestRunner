import yaml


def test_config_yaml_contract(tmp_path):
    config_file = tmp_path / "contract.yaml"
    config_file.write_text(
        """
test_name: contract_test

scenario:
  command: "echo contract_test"
  timeout_second: 1

artifact:
  output_dir: "runs/contract_test"
""",
        encoding="utf-8",
    )

    data = yaml.safe_load(config_file.read_text(encoding="utf-8"))

    assert isinstance(data, dict)
    assert "test_name" in data
    assert isinstance(data["test_name"], str)
    assert "scenario" in data
    assert isinstance(data["scenario"], dict)
    assert "artifact" in data
    assert isinstance(data["artifact"], dict)
    assert "step" not in data
