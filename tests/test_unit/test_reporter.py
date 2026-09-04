import json
from dataclasses import asdict
from pathlib import Path
from typing import List

import pytest

from runner.models import (
    ArtifactValidationResult,
    ExecutionSummary,
    FailureType,
    RunMetadata,
    RunResult,
    StepAttemptResult,
    StepResult,
)
from runner.reporter import JsonReporter


@pytest.mark.parametrize(
    argnames="metadata, summary, step_results, artifact_validation_results",
    argvalues=[
        (
            RunMetadata(
                test_case_id="test_case_001",
                test_case_name="Test Case 001",
                test_case_description="This is a test case.",
                device_serial="1234567890",
                device_product="Test Product",
                device_build="Test Build",
                runner_version="1.0.0",
                started_at="2024-01-01T00:00:00Z",
                finished_at="2024-01-01T00:10:00Z",
            ),
            ExecutionSummary(
                status="FAILED",
                configured_steps=3,
                executed_steps=3,
                passed_steps=2,
                failed_steps=1,
                skipped_steps=0,
                configured_artifact_rules=2,
                passed_artifact_rules=2,
                failed_artifact_rules=0,
                failed_required_artifact_rules=0,
                duration_seconds=600.0,
            ),
            [
                StepResult(
                    stage="setup",
                    name="Setup Step 1",
                    command="echo 'Setup 1'",
                    attempts=1,
                    success=True,
                    attempt_results=[
                        StepAttemptResult(
                            attempt=1,
                            success=True,
                            exit_code=0,
                            failure_type=FailureType.NONE,
                            duration_seconds=5.0,
                            stdout="Setup 1 completed.",
                            stderr="",
                            stdout_log_path="",
                            stderr_log_path="",
                        )
                    ],
                    duration_seconds=5.0,
                ),
                StepResult(
                    stage="test_stage",
                    name="Test Step 1",
                    command="echo 'Test 1'",
                    attempts=1,
                    success=True,
                    attempt_results=[
                        StepAttemptResult(
                            attempt=1,
                            success=True,
                            exit_code=0,
                            failure_type=FailureType.NONE,
                            duration_seconds=10.0,
                            stdout="Test 1 completed.",
                            stderr="",
                            stdout_log_path="",
                            stderr_log_path="",
                        )
                    ],
                    duration_seconds=10.0,
                ),
                StepResult(
                    stage="test_stage",
                    name="Test Step 2",
                    command="echo 'Test 2'",
                    attempts=1,
                    success=False,
                    attempt_results=[
                        StepAttemptResult(
                            attempt=1,
                            success=False,
                            failure_type=FailureType.PROCESS_ERROR,
                            exit_code=1,
                            duration_seconds=15.0,
                            stdout="Test 2 failed.",
                            stderr="",
                            stdout_log_path="",
                            stderr_log_path="",
                        )
                    ],
                    duration_seconds=15.0,
                ),
            ],
            [
                ArtifactValidationResult(
                    name="test_file_exists",
                    type="exists",
                    path="results/test_file.txt",
                    passed=True,
                    required=False,
                    message="File Exists",
                    failure_type=FailureType.NONE,
                ),
                ArtifactValidationResult(
                    name="test_file_size",
                    type="file_size",
                    path="results/test_file.txt",
                    passed=False,
                    required=True,
                    message="File size excede maxmium.",
                    actual_size_bytes=1,
                    failure_type=FailureType.ARTIFACT_INVALID,
                ),
            ],
        )
    ],
)
def test_save_result_json(
    tmp_path: Path,
    metadata: RunMetadata,
    summary: ExecutionSummary,
    step_results: List[StepResult],
    artifact_validation_results: List[ArtifactValidationResult],
):
    """Acceptance scenario.

    Given a completed run contains metadata, summaries, steps, and artifact results.
    When the reporter serializes the run result.
    Then the generated JSON preserves metadata, summary counts, step results, and artifact validation results.
    """

    run_result = RunResult(
        metadata=metadata,
        summary=summary,
        step_results=step_results,
        artifact_dir=str(tmp_path),
        artifact_validation_results=artifact_validation_results,
    )

    output_path = JsonReporter().save(result=run_result, output_dir=tmp_path)

    assert output_path.exists()
    assert output_path.name == "result.json"

    saved = json.loads(output_path.read_text(encoding="utf-8"))

    assert saved["metadata"] == asdict(metadata)
    assert saved["summary"] == asdict(summary)
    assert saved["step_results"] == [asdict(result) for result in step_results]
    assert saved["artifact_dir"] == str(tmp_path)
    assert saved["artifact_validation_results"] == [
        asdict(result) for result in artifact_validation_results
    ]
