from dataclasses import dataclass, field
from typing import List, Optional


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
class LifecycleStep:
    name: str
    type: str
    command: str
    timeout_second: int


@dataclass(frozen=True)
class LifecycleConfig:
    global_setup: List[LifecycleStep] = field(default_factory=list)
    setup: List[LifecycleStep] = field(default_factory=list)
    scenario: List[LifecycleStep] = field(default_factory=list)
    teardown: List[LifecycleStep] = field(default_factory=list)
    global_teardown: List[LifecycleStep] = field(default_factory=list)


@dataclass(frozen=True)
class ArtifactConfig:
    output_dir: str


@dataclass(frozen=True)
class RunnerConfig:

    test_case: DeviceTestCase
    device: DeviceInfo
    lifecycle: LifecycleConfig
    artifact: ArtifactConfig


@dataclass(frozen=True)
class StepResult:

    stage: str
    name: str
    command: str
    success: bool
    exit_code: Optional[int]
    duration_seconds: float
    stdout: str
    stderr: str
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


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
    duration_seconds: float


@dataclass(frozen=True)
class RunResult:

    metadata: RunMetadata
    summary: ExecutionSummary
    step_results: List[StepResult]
    artifact_dir: str | None = None

    @property
    def passed(self) -> bool:
        return all(result.exit_code == 0 for result in self.step_results)
