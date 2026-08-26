import csv
import json
from pathlib import Path
from typing import Any, Callable, List

from runner.models import ArtifactValidationResult, ArtifactValidationRule, FailureType


class ArtifactValidator:
    def __init__(self) -> None:
        self._handlers: dict[
            str, Callable[[ArtifactValidationRule, Path], ArtifactValidationResult]
        ] = {
            "exists": self._validate_exists,
            "file_size": self._validate_file_size,
            "file_extension": self._validate_file_extension,
            "directory_not_empty": self._validate_directory_not_empty,
            "csv_content": self._validate_csv_content,
            "json_content": self._validate_json_content,
        }

    def validate_all(
        self, rules: List[ArtifactValidationRule], base_dir: str | Path
    ) -> List[ArtifactValidationResult]:
        resolved_base_dir = Path(base_dir)

        return [self.validate(rule=rule, base_dir=resolved_base_dir) for rule in rules]

    def validate(
        self, rule: ArtifactValidationRule, base_dir: str | Path
    ) -> ArtifactValidationResult:
        resolved_base_dir = Path(base_dir)
        resolved_path = self._resolve_path(base_dir=resolved_base_dir, configured_path=rule.path)

        handler = self._handlers.get(rule.type)

        if handler is None:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(resolved_path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message=f"Unknown validation type: {rule.type}.",
            )

        try:
            return handler(rule, resolved_path)

        except OSError as error:

            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(resolved_path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message=f"Error during validation: {error}",
            )

    @staticmethod
    def _resolve_path(base_dir: str | Path, configured_path: str | Path) -> Path:
        resolved_base_dir = Path(base_dir)
        path = Path(configured_path)

        if path.is_absolute():
            return path

        return resolved_base_dir / path

    @staticmethod
    def _validate_exists(rule: ArtifactValidationRule, path: Path) -> ArtifactValidationResult:
        passed = path.exists()

        if passed:
            message = "Artifact exists."
        else:
            message = "Artifact does not exist."

        return ArtifactValidationResult(
            name=rule.name,
            type=rule.type,
            path=str(path),
            passed=passed,
            failure_type=FailureType.NONE if passed else FailureType.ARTIFACT_MISSING,
            message=message,
        )

    @staticmethod
    def _validate_file_size(rule: ArtifactValidationRule, path: Path) -> ArtifactValidationResult:
        if not path.exists():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_MISSING,
                message="File doesn't exist.",
            )

        if not path.is_file():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message="Artifact is not a file.",
            )

        actual_size = path.stat().st_size

        if rule.min_size_bytes is not None and actual_size < rule.min_size_bytes:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message=f"File size {actual_size} bytes is smaller than the minimum required size of {rule.min_size_bytes} bytes.",
                actual_size_bytes=actual_size,
            )

        if rule.max_size_bytes is not None and actual_size > rule.max_size_bytes:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message=f"File size {actual_size} bytes exceeds the maximum allowed size of {rule.max_size_bytes} bytes.",
                actual_size_bytes=actual_size,
            )

        return ArtifactValidationResult(
            name=rule.name,
            type=rule.type,
            path=str(path),
            passed=True,
            failure_type=FailureType.NONE,
            message=f"File size {actual_size} bytes is within the allowed range.",
            actual_size_bytes=actual_size,
        )

    @staticmethod
    def _validate_file_extension(
        rule: ArtifactValidationRule, path: Path
    ) -> ArtifactValidationResult:

        if not path.exists():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_MISSING,
                message="File doesn't exist.",
            )

        if not path.is_file():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message="Artifact is not a file.",
            )

        normalized_extensions = {
            ArtifactValidator._normalize_extensions(extension)
            for extension in rule.allowed_extensions
        }

        if not normalized_extensions:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message=("allowed_extensions cannot be empty."),
            )

        actual_extension = path.suffix.lower()

        passed = actual_extension in normalized_extensions

        if passed:
            message = f"File extension '{actual_extension}' is allowed."
        else:
            allowed = sorted(normalized_extensions)

            message = f"File extension '{actual_extension}' is not allowed entensions {allowed}."

        return ArtifactValidationResult(
            name=rule.name,
            type=rule.type,
            path=str(path),
            passed=passed,
            failure_type=FailureType.NONE if passed else FailureType.ARTIFACT_INVALID,
            message=message,
        )

    @staticmethod
    def _validate_directory_not_empty(
        rule: ArtifactValidationRule, path: Path
    ) -> ArtifactValidationResult:
        if not path.exists():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_MISSING,
                message="Directory doesn't exist.",
            )

        if not path.is_dir():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message="Artifact is not a directory.",
            )

        has_contents = next(path.iterdir(), None) is not None

        if has_contents:
            message = "Directory is not empty."
        else:
            message = "Directory is empty."

        return ArtifactValidationResult(
            name=rule.name,
            type=rule.type,
            path=str(path),
            passed=has_contents,
            failure_type=(FailureType.NONE if has_contents else FailureType.ARTIFACT_MISSING),
            message=message,
        )

    @staticmethod
    def _validate_csv_content(rule: ArtifactValidationRule, path: Path) -> ArtifactValidationResult:
        if not path.exists():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_MISSING,
                message="CSV file does not exists.",
            )
        if not path.is_file():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message="Artifact is not a file.",
            )

        try:
            with path.open("r", encoding="utf-8", newline="") as file:

                reader = csv.DictReader(file)

                if reader.fieldnames is None:
                    return ArtifactValidationResult(
                        name=rule.name,
                        type=rule.type,
                        path=str(path),
                        passed=False,
                        failure_type=FailureType.ARTIFACT_INVALID,
                        message="CSV header is missing.",
                    )

                actual_columns = {column.strip() for column in reader.fieldnames}

                missing_columns = [
                    column for column in rule.required_columns if column not in actual_columns
                ]

                if missing_columns:
                    return ArtifactValidationResult(
                        name=rule.name,
                        type=rule.type,
                        path=str(path),
                        passed=False,
                        failure_type=FailureType.ARTIFACT_INVALID,
                        message=f"CSV missing requred columns: {missing_columns}",
                    )

                row_count = sum(1 for _ in reader)

        except (csv.Error, UnicodeDecodeError) as error:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message=f"Unable to parse CSV: {error}",
            )

        if rule.min_rows is not None and row_count < rule.min_rows:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message=f"CSV contains {row_count} data rows, fewer than minimum {rule.min_rows}",
            )

        return ArtifactValidationResult(
            name=rule.name,
            type=rule.type,
            path=str(path),
            passed=True,
            failure_type=FailureType.NONE,
            message=f"CSV content is valid. Rows: {row_count}, coumns: {sorted(actual_columns)}.",
        )

    @staticmethod
    def _validate_json_content(
        rule: ArtifactValidationRule, path: Path
    ) -> ArtifactValidationResult:
        if not path.exists():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_MISSING,
                message="JSON file does not exists.",
            )

        if not path.is_file():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message="Artifact is not a file.",
            )

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)

        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message=f"Unable to parse JSON: {error}",
            )

        missing_paths = []

        for json_path in rule.required_json_paths:
            exists, _ = ArtifactValidator._get_json_path_value(data=data, json_path=json_path)

            if not exists:
                missing_paths.append(json_path)

        if missing_paths:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message=f"JSON missing required paths: {missing_paths}",
            )

        mismatches = []

        for json_path, expected_value in rule.expected_json_values.items():
            exists, actual_value = ArtifactValidator._get_json_path_value(
                data=data, json_path=json_path
            )

            if not exists:
                mismatches.append(f"{json_path}: path does not exist")

                continue

            if actual_value != expected_value:
                mismatches.append(
                    f"{json_path}: expected {expected_value!r}, actual {actual_value!r}"
                )

        if mismatches:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                failure_type=FailureType.ARTIFACT_INVALID,
                message=f"JSON value validation failed: {mismatches}",
            )

        return ArtifactValidationResult(
            name=rule.name,
            type=rule.type,
            path=str(path),
            passed=True,
            failure_type=FailureType.NONE,
            message="JSON content is valid.",
        )

    @staticmethod
    def _get_json_path_value(data: Any, json_path: str) -> tuple[bool, Any]:
        current = data

        for key in json_path.split("."):
            if not isinstance(current, dict):
                return False, None

            if key not in current:
                return False, None

            current = current[key]

        return True, current

    @staticmethod
    def _normalize_extensions(extension: str) -> str:
        normalized = extension.strip().lower()

        if not normalized.startswith("."):
            normalized = "." + normalized

        return normalized
