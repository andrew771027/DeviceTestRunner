import re
from datetime import datetime, timezone
from pathlib import Path


class ArtifactManager:
    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def create_run_directory(self, test_case_id: str) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d_%H_%M_%S")

        safe_test_case_id = self._sanitize_name(test_case_id)

        run_dir = self.output_dir / f"{safe_test_case_id}_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def save_step_stdout(self, run_dir: Path, stage: str, step_name: str, stdout: str) -> Path:
        stage_dir = run_dir / self._sanitize_name(stage)

        stage_dir.mkdir(parents=True, exist_ok=True)

        safe_step_name = self._sanitize_name(step_name)

        output_path = stage_dir / f"{safe_step_name}.stdout.log"

        output_path.write_text(stdout, encoding="utf-8")

        return output_path

    def save_step_stderr(self, run_dir: Path, stage: str, step_name: str, stderr: str) -> Path:
        stage_dir = run_dir / self._sanitize_name(stage)

        stage_dir.mkdir(parents=True, exist_ok=True)

        safe_step_name = self._sanitize_name(step_name)

        output_path = stage_dir / f"{safe_step_name}.stderr.log"

        output_path.write_text(stderr, encoding="utf-8")

        return output_path

    @staticmethod
    def _sanitize_name(name: str) -> str:

        sanitized = re.sub(
            r"[^A-Za-z0-9_.-]+",
            "_",
            name,
        )
        return sanitized.strip("_") or "unnamed"
