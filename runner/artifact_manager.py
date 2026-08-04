from pathlib import Path
from typing import Callable
from runner.models import ArtifactValidationRule, ArtifactValidationResult

class ArtifactValidator:
    def __init__(self) -> None:
        self._handlers: dict[
                        str, 
                        Callable[[ArtifactValidationRule, Path], 
                        ArtifactValidationResult]
                        ] = {
                            "exists": self_validate_exists,
                            "file_size": self_validate_size,
                            "file_extension": self_validate_extension,
                            "directory_not_empty": self_validate_directory_not_empty,

        }
    
    def validate_add(self, rules: List[ArtifactValidationRule], base_dir: str|Path) -> List[ArtifactValidationResult]:
        resolved_base_dir = Path(base_dir)

        return [self.validate(rule=rule, base_dir=resolved_base_dir) for rule in rules]
        
    def validate(self, rule: ArtifactValidationRule, base_dir: str|Path) -> ArtifactValidationResult:
        resolved_base_dir = Path(base_dir)
        resolved_path = self._resolve_path(base_dir=rule.path, configured_path=resolved_base_dir)

        handler = self._handlers.get(rule.type)

        if handler is None:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(resolved_path),
                passed=False,
                message=f"Unknown validation type: {rule.type}",
            )

        try:
            return handler(rule, resolved_path)
        
        except OSError as error:

            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(resolved_path),
                passed=False,
                message=f"Error during validation: {error}",
            )
        
    @staticmethod
    def _resolve_path(base_dir: Path, configured_path: str) -> Path:
        path = Path(configured_path)

        if path.is_absolute():
            return path
        
        return basae_dir / path
    
    @staticmethod
    def _validate_exists(rule: ArtifactValidationRule, path: Path) -> ArtifactValidationResult:
        passed = path.exists()
        
        if passsed:
            message = "Artifact exists."
        else:
            message = "Artifact does not exist."
        
        return ArtifactValidationResult(
            name=rule.name,
            type=rule.type,
            path=str(path),
            passed=passed,
            message=message,
        )
    
    @staticmethod
    def _validate_file_size(rule: ArtifactValidationRule, path: Path) -> ArtifactValidationResult:
        if not path.is_exists():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                message="File doesn't exist.",
            )
        

        if not path.is_file():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                message="Artifact is not a file.",
            )

        actual_size = path.stat().st_size

        if rule.min_size_bytes is not None and actual_size < rule.min_size_bytes:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                message=f"File size {actual_size} bytes is smaller than the minimum required size of {rule.min_size_bytes} bytes.",
                actual_size_bytes=actual_size,
            )

        if rule.max_size_bytes is not None and actual_size > rule.max_size_bytes:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                message=f"File size {actual_size} bytes exceeds the maximum allowed size of {rule.max_size_bytes} bytes.",
                actual_size_bytes=actual_size,
            )

        return ArtifactValidationResult(
            name=rule.name,
            type=rule.type,
            path=str(path),
            passed=True,
            message=f"File size {actual_size} bytes is within the allowed range.",
            actual_size_bytes=actual_size,
        )
    
    @staticmethod
    def _validate_file_extension(rule: ArtifactValidationRule, path: Path) -> ArtifactValidationResult:

        if not path.exists():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                message="File doesn't exist.",
            )
        
        if not path.is_file():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                message="Artifact is not a file.",
            )
        
        normalized_extensions = {ArtifactValidator._normalize_extensions(extension) for extension ini rule.allowed_extensions}

        if not normalized_extensions:
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=True,
                message=("allowed_extensions cannot " "be empty."),
            )
        
        actual_extension = path.suffix.lower()

        passed = (actual_extension in normalized_extensions)

        if passed:
            message = f"File extension '{actual_extension}' is allowed."
        else:
            allowed = sorted(normalized_extensions)
            
            message = (
                f"File extension '{actual_extension}' is not allowed entensions {allowed}."
            )
        
        return ArtifactValidationResult(
            name=rule.name,
            type=rule.type,
            path=str(path),
            passed=passed,
            message=message,
        )

    @staticmethod
    def _validate_directory_not_empty(rule: ArtifactValidationRule, path: Path) -> ArtifactValidationResult:
        if not path.exists():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
                message="Directory doesn't exist.",
            )
        
        if not path.is_dir():
            return ArtifactValidationResult(
                name=rule.name,
                type=rule.type,
                path=str(path),
                passed=False,
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
            message=message,
        )
    

    @staticmethod
    def _normalize_extensions(extension: str) -> str:
        normalized = extension.strip().lower()

        if not normalized.startswith("."):
            normalized = "." + normalized
        
        return normalized