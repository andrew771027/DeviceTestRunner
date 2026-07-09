from dataclasses import dataclass
from typing import Optional


@dataclass
class ScenarioConfig:
    command: str
    timeout_second: int


@dataclass
class ArtifactConfig:
    output_dir: str


@dataclass
class TestConfig:

    __test__ = False

    test_name: str
    scenario: ScenarioConfig
    artifact: ArtifactConfig


@dataclass
class TestResult:

    __test__ = False

    test_name: str
    command: str
    success: bool
    exit_code: Optional[int]
    duration: float
    stdout: str
    stderr: str
    error: Optional[str] = None
