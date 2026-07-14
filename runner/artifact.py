import json
from pathlib import Path
from typing import Any


class ArtifactManager:
    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)

    def create_run_directory(self, test_case_id: str) -> Path:
        run_dir = self.output_dir / test_case_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def save_stdout(self, run_dir: Path, step_name: str, stdout: str) -> Path:
        output_path = run_dir / f"{step_name}.stdout.log"
        output_path.write_text(stdout, encoding="utf-8")
        return output_path

    def save_stderr(self, run_dir: Path, step_name: str, stderr: str) -> Path:
        output_path = run_dir / f"{step_name}.stderr.log"
        output_path.write_text(stderr, encoding="utf-8")
        return output_path
