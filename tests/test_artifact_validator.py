from pathlib import Path
from runner.artifact_validator import ArtifactValidator
from runner.models import ArtifactValidationRule

def test_exists_rule_passes_when_file_exists(tmp_path: Path):
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

def test_exists_rule_fails_when_file_missing(tmp_path: Path):
    rule = ArtifactValidationRule(
        name="missing_file.txt",
        type="exists",
        path="missing_file.txt"
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "missing_file.txt"
    assert result.type == "exists"
    assert result.message == "Artifact does not exist."

def test_file_size_rule_passes_within_range(tmp_path: Path):
    target = tmp_path / "test_file.txt"
    target.write_bytes(b"1234567890")  # 10 bytes

    rule = ArtifactValidationRule(
        name="test_file.txt",
        type="file_size",
        path="test_file.txt",
        min_size_bytes=5,
        max_size_bytes=20
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is True
    assert result.name == "test_file.txt"
    assert result.type == "file_size"
    assert result.path == str(target)
    assert result.actual_size_bytes == 10

def test_file_size_rule_fails_below_minimum(tmp_path: Path):
    target = tmp_path / "test_file.txt"
    target.write_bytes(b"1234") # 4 bytes

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
    assert result.message == f"File size {result.actual_size_bytes} bytes is smaller than the minimum required size of {rule.min_size_bytes} bytes."

def test_file_size_rule_fails_above_maximum(tmp_path: Path):
    target = tmp_path / "test_file.txt"
    target.write_bytes(b"123456789012345678901234567890") # 30 bytes

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
    assert result.message == f"File size {result.actual_size_bytes} bytes exceeds the maximum allowed size of {rule.max_size_bytes} bytes."

def test_file_size_rule_fails_when_missing(tmp_path: Path):
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

def test_file_size_rule_fails_for_directory(tmp_path: Path):
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

def test_file_extension_rule_passes(tmp_path: Path):
    target = tmp_path / "test_file.txt"
    target.write_text("Hello, world!", encoding="utf-8")

    rule = ArtifactValidationRule(
        name="test_file.txt",
        type="file_extension",
        path="test_file.txt",
        allowed_extensions=[".txt", ".md"]
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is True
    assert result.name == "test_file.txt"
    assert result.type == "file_extension"
    assert result.path == str(target)
    assert result.message == f"File extension '{target.suffix}' is allowed."

def test_file_extension_rule_fails(tmp_path: Path):
    target = tmp_path / "test_file.pdf"
    target.write_text("Hello, world!", encoding="utf-8")

    rule = ArtifactValidationRule(
        name="test_file.pdf",
        type="file_extension",
        path="test_file.pdf",
        allowed_extensions=[".txt", ".md"]
    )

    result = ArtifactValidator().validate(rule=rule, base_dir=tmp_path)

    assert result.passed is False
    assert result.name == "test_file.pdf"
    assert result.type == "file_extension"
    assert result.path == str(target)
    assert result.message == f"File extension '{target.suffix}' is not allowed entensions {sorted(rule.allowed_extensions)}."

def test_file_extension_rule_requires_extensions(tmp_path: Path):
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