from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DeviceTestCase:
    id: str
    name: str
    description: str


@dataclass
class DeviceInfo:
    serial: str
    product: str
    build: str


@dataclass
class WorkflowStep:
    name: str
    type: str
    command: str
    timeout_second: int


@dataclass
class Workflow:
    steps: List[WorkflowStep]


@dataclass
class ArtifactConfig:
    output_dir: str


@dataclass
class RunnerConfig:

    test_case: DeviceTestCase
    device: DeviceInfo
    workflow: Workflow
    artifact: ArtifactConfig


@dataclass
class StepResult:

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


@dataclass
class RunMetadata:
    test_case_id: str
    test_case_name: str
    device_serial: str
    device_product: str
    device_build: str
    runner_version: str


@dataclass
class ExecutionSummary:
    status: str
    total_steps: int
    passed_steps: int
    failed_steps: int
    duration_seconds: float


@dataclass
class RunResult:

    metadata: RunMetadata
    summary: ExecutionSummary
    step_results: List[StepResult]
    artifact_dir: str | None = None

    @property
    def passed(self) -> bool:
        return all(result.exit_code == 0 for result in self.step_results)
