from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class FailureType(str, Enum):
    NONE = "none"

    TIMEOUT = "tiimeout"
    DEVICE_OFFLINE = "device_offline"
    PROCESS_ERROR = "process_error"

    ARTIFACT_MISSING = "artifact_missing"
    ARTIFACT_INVALID = "artifact_invalid"


@dataclass(frozen=True)
class DeviceTestCase:

    id: str
    name: str
    description: str


@dataclass(frozen=True)
class DeviceInfo:

    serial: str
    product: str
    build: str


@dataclass(frozen=True)
class LifecycleStepContent:

    name: str
    type: str
    command: str
    timeout_second: int


@dataclass(frozen=True)
class LifecycleSteps:

    steps: List[LifecycleStepContent] = field(default_factory=list)


@dataclass(frozen=True)
class LifecycleConfig:

    global_setup: LifecycleSteps = field(default_factory=LifecycleSteps)
    setup: LifecycleSteps = field(default_factory=LifecycleSteps)
    scenario: LifecycleSteps = field(default_factory=LifecycleSteps)
    teardown: LifecycleSteps = field(default_factory=LifecycleSteps)
    global_teardown: LifecycleSteps = field(default_factory=LifecycleSteps)


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 1
    delay_seconds: float = 0.0
    retry_on: tuple[FailureType, ...] = ()

    retry_on: list[FailureType] = field(
        default_factory=lambda: [
            FailureType.TIMEOUT,
            FailureType.DEVICE_OFFLINE,
            FailureType.PROCESS_ERROR,
            FailureType.ARTIFACT_MISSING,
            FailureType.ARTIFACT_INVALID,
        ]
    )


@dataclass(frozen=True)
class ArtifactValidationRule:

    name: str
    type: str
    path: str

    # v1.5.1
    after_step: Optional[str] = None
    # v1.5.3
    required: bool = True

    # file_size
    max_size_bytes: Optional[int] = None
    min_size_bytes: Optional[int] = None

    # file_extension
    allowed_extensions: List[str] = field(default_factory=list)

    # csv_content
    required_columns: list[str] = field(default_factory=list)
    min_rows: Optional[int] = None

    # json_content
    required_json_paths: list[str] = field(default_factory=list)
    expected_json_values: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArtifactValidationConfig:

    rules: List[ArtifactValidationRule] = field(default_factory=list)


@dataclass(frozen=True)
class ArtifactConfig:
    output_dir: str
    validation: ArtifactValidationConfig = field(default_factory=ArtifactValidationConfig)


@dataclass(frozen=True)
class RunnerConfig:

    test_case: DeviceTestCase
    device: DeviceInfo
    lifecycle: LifecycleConfig
    retry: RetryConfig
    artifact: ArtifactConfig


@dataclass(frozen=True)
class ArtifactValidationResult:
    name: str
    type: str
    path: str
    passed: bool
    message: str
    # v1.5.3
    required: bool

    failure_type: FailureType

    actual_size_bytes: Optional[int] = None


@dataclass(frozen=True)
class StepAttemptResult:
    attempt: int
    success: bool
    failure_type: FailureType
    exit_code: Optional[int]
    duration_seconds: float

    # subprocess 完整輸出

    stdout: str
    stderr: str

    # 對應 artifact 檔案位置

    stdout_log_path: str
    stderr_log_path: str
    error: str = ""

    # v1.5.1
    artifact_validation_results: list[ArtifactValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


@dataclass(frozen=True)
class StepResult:
    stage: str
    name: str
    command: str
    attempts: int
    success: bool
    attempt_results: list[StepAttemptResult]
    duration_seconds: float


@dataclass(frozen=True)
class RunMetadata:
    test_case_id: str
    test_case_name: str
    test_case_description: str
    device_serial: str
    device_product: str
    device_build: str
    runner_version: str
    started_at: str
    finished_at: str


@dataclass(frozen=True)
class ExecutionSummary:
    status: str
    configured_steps: int
    executed_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int

    configured_artifact_rules: int
    passed_artifact_rules: int
    failed_artifact_rules: int
    failed_required_artifact_rules: int

    duration_seconds: float


@dataclass(frozen=True)
class RunResult:

    metadata: RunMetadata
    summary: ExecutionSummary
    step_results: List[StepResult]
    artifact_dir: str | None = None
    artifact_validation_results: List[ArtifactValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(step_result.success for step_result in self.step_results)
