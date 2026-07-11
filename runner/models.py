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


@dataclass
class RunResult:

    test_case_id: str
    test_case_name: str
    success: bool
    step_results: List[StepResult]

    @property
    def passed(self) -> bool:
        return all(result.exit_code == 0 for result in self.step_results)
