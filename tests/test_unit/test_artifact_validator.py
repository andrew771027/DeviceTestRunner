import json
from pathlib import Path

from runner.artifact_validator import ArtifactValidator
from runner.models import ArtifactValidationRule, FailureType


def test_exists_rule_passes_when_file_exists(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then exists rule is accepted when file exists.
    """
    target = tmp_path / "test_file.txt"
    target.write_text("Hello, world!", encoding="utf-8")

    rule = ArtifactValidationRule(
        name="test_file.txt",
        type="exists",
        path="test_file.txt",
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is True
    assert result.name == "test_file.txt"
    assert result.type == "exists"
    assert result.path == str(target)
    assert result.message == "Artifact exists."
    assert result.failure_type == FailureType.NONE


def test_exists_rule_fails_when_file_missing(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then exists rule is rejected when file missing, with a diagnostic failure result.
    """
    rule = ArtifactValidationRule(name="missing_file.txt", type="exists", path="missing_file.txt")

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "missing_file.txt"
    assert result.type == "exists"
    assert result.message == "Artifact does not exist."
    assert result.failure_type == FailureType.ARTIFACT_MISSING


def test_file_size_rule_passes_within_range(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then file size rule passes within range.
    """
    target = tmp_path / "test_file.txt"
    target.write_bytes(b"1234567890")  # 10 bytes

    rule = ArtifactValidationRule(
        name="test_file.txt",
        type="file_size",
        path="test_file.txt",
        min_size_bytes=5,
        max_size_bytes=20,
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is True
    assert result.name == "test_file.txt"
    assert result.type == "file_size"
    assert result.path == str(target)
    assert result.actual_size_bytes == 10
    assert result.failure_type == FailureType.NONE


def test_file_size_rule_fails_below_minimum(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then file size rule rejects minimum and reports the applicable validation failure.
    """
    target = tmp_path / "test_file.txt"
    target.write_bytes(b"1234")  # 4 bytes

    rule = ArtifactValidationRule(
        name="test_file.txt",
        type="file_size",
        path="test_file.txt",
        min_size_bytes=5,
        max_size_bytes=20,
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "test_file.txt"
    assert result.type == "file_size"
    assert result.path == str(target)
    assert result.actual_size_bytes == 4
    assert (
        result.message
        == f"File size {result.actual_size_bytes} bytes is smaller than the minimum required size of {rule.min_size_bytes} bytes."
    )
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_file_size_rule_fails_above_maximum(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then file size rule rejects maximum and reports the applicable validation failure.
    """
    target = tmp_path / "test_file.txt"
    target.write_bytes(b"123456789012345678901234567890")  # 30 bytes

    rule = ArtifactValidationRule(
        name="test_file.txt",
        type="file_size",
        path="test_file.txt",
        min_size_bytes=5,
        max_size_bytes=20,
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "test_file.txt"
    assert result.type == "file_size"
    assert result.path == str(target)
    assert result.actual_size_bytes == 30
    assert (
        result.message
        == f"File size {result.actual_size_bytes} bytes exceeds the maximum allowed size of {rule.max_size_bytes} bytes."
    )
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_file_size_rule_fails_when_missing(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then file size rule is rejected when missing, with a diagnostic failure result.
    """
    rule = ArtifactValidationRule(
        name="test_file.txt",
        type="file_size",
        path="testfile.txt",
        min_size_bytes=1,
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "test_file.txt"
    assert result.type == "file_size"
    assert result.message == "File doesn't exist."
    assert result.failure_type == FailureType.ARTIFACT_MISSING


def test_file_size_rule_fails_for_directory(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then file size rule rejects directory and reports the applicable validation failure.
    """
    directory = tmp_path / "test_output"
    directory.mkdir()

    rule = ArtifactValidationRule(
        name="test_output",
        type="file_size",
        path="test_output",
        min_size_bytes=5,
        max_size_bytes=20,
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.message == "Artifact is not a file."
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_file_extension_rule_passes(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then file extension rule passes.
    """
    target = tmp_path / "test_file.txt"
    target.write_text("Hello, world!", encoding="utf-8")

    rule = ArtifactValidationRule(
        name="test_file.txt",
        type="file_extension",
        path="test_file.txt",
        allowed_extensions=[".txt", ".md"],
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is True
    assert result.name == "test_file.txt"
    assert result.type == "file_extension"
    assert result.path == str(target)
    assert result.message == f"File extension '{target.suffix}' is allowed."
    assert result.failure_type == FailureType.NONE


def test_file_extension_rule_fails(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then file extension rule fails.
    """
    target = tmp_path / "test_file.pdf"
    target.write_text("Hello, world!", encoding="utf-8")

    rule = ArtifactValidationRule(
        name="test_file.pdf",
        type="file_extension",
        path="test_file.pdf",
        allowed_extensions=[".txt", ".md"],
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "test_file.pdf"
    assert result.type == "file_extension"
    assert result.path == str(target)
    assert (
        result.message
        == f"File extension '{target.suffix}' is not allowed entensions {sorted(rule.allowed_extensions)}."
    )
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_file_extension_rule_requires_extensions(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then file extension rule requires extensions.
    """
    target = tmp_path / "test_file.txt"
    target.write_text("Hello World!!", encoding="utf-8")

    rule = ArtifactValidationRule(
        name="test_file",
        type="file_extension",
        path="test_file.txt",
        allowed_extensions=[],
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.message == "allowed_extensions cannot be empty."
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_directory_not_empty_passes(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then directory not empty passes.
    """
    directory = tmp_path / "test_directory"
    directory.mkdir()
    (directory / "test_file.txt").write_text("Hello World!", encoding="utf-8")

    rule = ArtifactValidationRule(
        name="test_directory", type="directory_not_empty", path="test_directory"
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is True
    assert result.name == "test_directory"
    assert result.type == "directory_not_empty"
    assert result.path == str(directory)
    assert result.message == "Directory is not empty."
    assert result.failure_type == FailureType.NONE


def test_directory_not_empty_fails_when_empty(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then directory not empty is rejected when empty, with a diagnostic failure result.
    """
    directory = tmp_path / "test_directory"
    directory.mkdir()

    rule = ArtifactValidationRule(
        name="test_directory", type="directory_not_empty", path="test_directory"
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "test_directory"
    assert result.type == "directory_not_empty"
    assert result.path == str(directory)
    assert result.message == "Directory is empty."
    assert result.failure_type == FailureType.ARTIFACT_MISSING


def test_directory_not_empty_fails_for_file(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then directory not empty rejects file and reports the applicable validation failure.
    """
    target = tmp_path / "test_file"
    target.write_text("Hello World!", encoding="utf-8")

    rule = ArtifactValidationRule(name="test_file", type="directory_not_empty", path="test_file")

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.message == "Artifact is not a directory."
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_unsupported_validation_type_fails(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then unsupported validation type fails.
    """
    rule = ArtifactValidationRule(name="unknown_rule", type="unsupported_type", path="output.txt")

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "unknown_rule"
    assert result.type == "unsupported_type"
    assert result.message == f"Unknown validation type: {rule.type}."
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_validate_all_returns_all_results(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then validate all returns all results without altering the source data.
    """
    target = tmp_path / "exists.txt"
    target.write_text("Hello world!", encoding="utf-8")

    rules = [
        ArtifactValidationRule(
            name="existing",
            type="exists",
            path="exists.txt",
        ),
        ArtifactValidationRule(
            name="missing",
            type="exists",
            path="missing.txt",
        ),
    ]

    results = ArtifactValidator().validate_all(rules=rules, base_dir=tmp_path)

    assert len(results) == 2
    assert results[0].passed is True
    assert results[1].passed is False
    assert results[0].failure_type == FailureType.NONE
    assert results[1].failure_type == FailureType.ARTIFACT_MISSING


def test_csv_content(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then a CSV satisfying the required header, columns, and row count is accepted.
    """

    target = tmp_path / "test_csv_file.csv"
    target.write_text("timestamp,power,voltage\n" "1,100,4.2\n" "2,120,4.1\n", encoding="utf-8")

    rule = ArtifactValidationRule(
        name="csv_content",
        type="csv_content",
        path="test_csv_file.csv",
        required_columns=["timestamp", "power"],
        min_rows=2,
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is True
    assert result.name == "csv_content"
    assert result.type == "csv_content"
    assert "CSV content is valid" in result.message
    assert result.failure_type == FailureType.NONE


def test_csv_content_fails_when_header_missing(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then CSV content is rejected when header missing, with a diagnostic failure result.
    """

    target = tmp_path / "test_csv_file.csv"
    target.write_text(
        "",
        encoding="utf-8",
    )

    rule = ArtifactValidationRule(
        name="csv_content",
        type="csv_content",
        path="test_csv_file.csv",
        required_columns=["timestamp", "power"],
        min_rows=1,
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.message == ("CSV header is missing.")
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_csv_content_fails_when_column_missing(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then CSV content is rejected when column missing, with a diagnostic failure result.
    """

    target = tmp_path / "test_csv_file.csv"
    target.write_text("timestamp,voltage\n" "1,4.2\n" "2,4.1\n", encoding="utf-8")

    rule = ArtifactValidationRule(
        name="csv_content",
        type="csv_content",
        path="test_csv_file.csv",
        required_columns=["timestamp", "power"],
        min_rows=2,
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "csv_content"
    assert result.type == "csv_content"
    assert result.message == "CSV missing requred columns: ['power']"
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_csv_content_fails_when_raw_too_few(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then CSV content is rejected when raw too few, with a diagnostic failure result.
    """

    target = tmp_path / "test_csv_file.csv"
    target.write_text(
        ("timestamp,power\n" "1,100\n"),
        encoding="utf-8",
    )

    rule = ArtifactValidationRule(
        name="csv_content",
        type="csv_content",
        path="test_csv_file.csv",
        required_columns=["timestamp", "power"],
        min_rows=2,
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "csv_content"
    assert result.type == "csv_content"
    assert result.message == f"CSV contains 1 data rows, fewer than minimum {rule.min_rows}"
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_csv_content_fails_when_only_header(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then CSV content is rejected when only header, with a diagnostic failure result.
    """

    target = tmp_path / "test_csv_file.csv"
    target.write_text(
        "timestamp,power\n",
        encoding="utf-8",
    )

    rule = ArtifactValidationRule(
        name="csv_content",
        type="csv_content",
        path="test_csv_file.csv",
        required_columns=["timestamp", "power"],
        min_rows=1,
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "csv_content"
    assert result.type == "csv_content"
    assert result.message == f"CSV contains 0 data rows, fewer than minimum {rule.min_rows}"
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_csv_content_fails_when_file_missing(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then CSV content is rejected when file missing, with a diagnostic failure result.
    """

    rule = ArtifactValidationRule(
        name="csv_content",
        type="csv_content",
        path="test_csv_file.csv",
        required_columns=["timestamp", "power"],
        min_rows=1,
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "csv_content"
    assert result.type == "csv_content"
    assert result.message == "CSV file does not exists."
    assert result.failure_type == FailureType.ARTIFACT_MISSING


def test_csv_content_fails_when_encoding_not_utf8(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then CSV content is rejected when encoding not UTF-8, with a diagnostic failure result.
    """
    target = tmp_path / "test_csv_file.csv"
    target.write_bytes(b"\xff\xfe\xfd\xfc")

    rule = ArtifactValidationRule(
        name="csv_content",
        type="csv_content",
        path="test_csv_file.csv",
        required_columns=["timestamp"],
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert "Unable to parse CSV" in (result.message)
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_csv_content_fails_when_path_is_directory(
    tmp_path: Path,
):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then CSV content is rejected when path is directory, with a diagnostic failure result.
    """
    target = tmp_path / "output"
    target.mkdir()

    rule = ArtifactValidationRule(
        name="csv_content",
        type="csv_content",
        path="output",
    )

    result = ArtifactValidator().validate(
        rule=rule,
        base_dir=tmp_path,
    )

    assert result.passed is False
    assert result.message == ("Artifact is not a file.")
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_json_content(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then a JSON document satisfying the required paths and values is accepted.
    """

    target = tmp_path / "test_json_file.json"
    target.write_text(
        json.dumps(
            {
                "status": "PASSED",
                "metrics": {
                    "average_power": 110.0,
                    "sample_count": 2,
                },
            }
        ),
        encoding="utf-8",
    )

    rule = ArtifactValidationRule(
        name="json_content",
        type="json_content",
        path="test_json_file.json",
        required_json_paths=["status", "metrics.average_power", "metrics.sample_count"],
        expected_json_values={"status": "PASSED", "metrics.sample_count": 2},
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is True
    assert result.message == "JSON content is valid."
    assert result.failure_type == FailureType.NONE


def test_json_content_fails_when_path_missing(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then JSON content is rejected when path missing, with a diagnostic failure result.
    """
    target = tmp_path / "test_json_file.json"
    target.write_text(
        json.dumps(
            {
                "status": "PASSED",
                "metrics": {
                    "sample_count": 2,
                },
            }
        ),
        encoding="utf-8",
    )

    rule = ArtifactValidationRule(
        name="json_content",
        type="json_content",
        path="test_json_file.json",
        required_json_paths=[
            "status",
            "metrics.average_power",
        ],
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.message == "JSON missing required paths: ['metrics.average_power']"
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_json_content_fails_when_file_missing(
    tmp_path: Path,
):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then JSON content is rejected when file missing, with a diagnostic failure result.
    """
    rule = ArtifactValidationRule(
        name="json_content",
        type="json_content",
        path="missing.json",
        required_json_paths=[
            "status",
        ],
    )

    result = ArtifactValidator().validate(
        rule=rule,
        base_dir=tmp_path,
    )

    assert result.passed is False
    assert result.message == ("JSON file does not exists.")
    assert result.failure_type == FailureType.ARTIFACT_MISSING


def test_json_content_fails_when_value_mismatch(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then JSON content is rejected when value mismatch, with a diagnostic failure result.
    """
    target = tmp_path / "test_json_file.json"
    target.write_text(
        json.dumps({"status": "FAILED", "metrics": {"sample_count": 2}}),
        encoding="utf-8",
    )

    rule = ArtifactValidationRule(
        name="json_content",
        type="json_content",
        path="test_json_file.json",
        expected_json_values={
            "status": "PASSED",
        },
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert (
        result.message
        == "JSON value validation failed: [\"status: expected 'PASSED', actual 'FAILED'\"]"
    )
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_json_content_fails_when_json_invalid(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then JSON content is rejected when JSON invalid, with a diagnostic failure result.
    """
    target = tmp_path / "test_json_file.json"
    target.write_text(""" { "status": "PASSED", } """, encoding="utf-8")

    rule = ArtifactValidationRule(
        name="json_content", type="json_content", path="test_json_file.json"
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert "Unable to parse JSON" in result.message
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_json_expected_value_fails_when_path_missing(
    tmp_path: Path,
):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then JSON expected value is rejected when path missing, with a diagnostic failure result.
    """
    target = tmp_path / "result.json"

    target.write_text(
        json.dumps(
            {
                "status": "PASSED",
            }
        ),
        encoding="utf-8",
    )

    rule = ArtifactValidationRule(
        name="json_content",
        type="json_content",
        path="result.json",
        expected_json_values={
            "metrics.sample_count": 2,
        },
    )

    result = ArtifactValidator().validate(
        rule=rule,
        base_dir=tmp_path,
    )

    assert result.passed is False
    assert "path does not exist" in (result.message)
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_json_number_string_type_mismatch(
    tmp_path: Path,
):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then JSON number string type mismatch.
    """
    target = tmp_path / "result.json"

    target.write_text(
        json.dumps(
            {
                "sample_count": "2",
            }
        ),
        encoding="utf-8",
    )

    rule = ArtifactValidationRule(
        name="json_content",
        type="json_content",
        path="result.json",
        expected_json_values={
            "sample_count": 2,
        },
    )

    result = ArtifactValidator().validate(
        rule=rule,
        base_dir=tmp_path,
    )

    assert result.passed is False
    assert result.failure_type == FailureType.ARTIFACT_INVALID


def test_json_content_expected_boolean_matches(
    tmp_path: Path,
):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then JSON content expected boolean matches.
    """
    target = tmp_path / "test_json_file.json"

    target.write_text(
        json.dumps(
            {
                "valid": True,
            }
        ),
        encoding="utf-8",
    )

    rule = ArtifactValidationRule(
        name="json_content",
        type="json_content",
        path="test_json_file.json",
        expected_json_values={
            "valid": True,
        },
    )

    result = ArtifactValidator().validate(
        rule=rule,
        base_dir=tmp_path,
    )

    assert result.passed is True
    assert result.message == ("JSON content is valid.")
    assert result.failure_type == FailureType.NONE


def test_get_json_path_value_returns_nested_value():
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then get JSON path value returns nested value without altering the source data.
    """
    data = {"metrics": {"power": {"average": 123.5}}}

    exists, value = ArtifactValidator._get_json_path_value(
        data=data, json_path="metrics.power.average"
    )

    assert exists is True
    assert value == 123.5


def test_get_json_path_value_returns_false_when_missing():
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then get JSON path value returns false when missing without altering the source data.
    """
    data = {"metrics": {"power": {}}}

    exists, value = ArtifactValidator._get_json_path_value(
        data=data, json_path="metrics.power.average"
    )

    assert exists is False
    assert value is None


def test_directory_missing_is_artifact_missing(tmp_path: Path):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then directory missing is artifact missing.
    """
    rule = ArtifactValidationRule(
        name="recorder",
        type="directory_not_empty",
        path="recorder",
    )

    result = ArtifactValidator().validate(
        rule=rule,
        base_dir=tmp_path,
    )

    assert result.passed is False

    assert result.failure_type == FailureType.ARTIFACT_MISSING


def test_non_empty_directory_passes(
    tmp_path: Path,
):
    """Acceptance scenario.

    Given an artifact validation rule and its filesystem state are configured.
    When the artifact validator evaluates the rule.
    Then non empty directory passes.
    """
    directory = tmp_path / "recorder"

    directory.mkdir()

    (directory / "power.csv").write_text(
        "power",
        encoding="utf-8",
    )

    rule = ArtifactValidationRule(
        name="recorder",
        type="directory_not_empty",
        path="recorder",
    )

    result = ArtifactValidator().validate(
        rule=rule,
        base_dir=tmp_path,
    )

    assert result.passed is True

    assert result.failure_type == FailureType.NONE
