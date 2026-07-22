import json
from dataclasses import asdict
from pathlib import Path
from typing import List

import pytest

from runner.models import ExecutionSummary, RunMetadata, RunResult, StepResult
from runner.reporter import JsonReporter


@pytest.mark.parametrize(
    argnames="metadata, summary, step_results",
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
                duration_seconds=600.0,
            ),
            [
                StepResult(
                    stage="setup",
                    name="Setup Step 1",
                    command="echo 'Setup 1'",
                    success=True,
                    exit_code=0,
                    duration_seconds=5.0,
                    stdout="Setup 1 completed.",
                    stderr="",
                ),
                StepResult(
                    stage="test_stage",
                    name="Test Step 1",
                    command="echo 'Test 1'",
                    success=True,
                    exit_code=0,
                    duration_seconds=10.0,
                    stdout="Test 1 completed.",
                    stderr="",
                ),
                StepResult(
                    stage="test_stage",
                    name="Test Step 2",
                    command="echo 'Test 2'",
                    success=False,
                    exit_code=1,
                    duration_seconds=15.0,
                    stdout="Test 2 failed.",
                    stderr="",
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
):

    run_result = RunResult(
        metadata=metadata,
        summary=summary,
        step_results=step_results,
        artifact_dir=str(tmp_path),
    )

    output_path = JsonReporter().save(result=run_result, output_dir=tmp_path)

    assert output_path.exists()
    assert output_path.name == "result.json"

    saved = json.loads(output_path.read_text(encoding="utf-8"))

    assert saved["metadata"] == asdict(metadata)
    assert saved["summary"] == asdict(summary)
    assert saved["step_results"] == [asdict(result) for result in step_results]
