import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, TextIO

from runner.models import ArtifactValidationRule


class StepLogWriter:
    """負責單一 step 的 stdout/stderr。"""

    def __init__(
        self,
        stage: str,
        step_name: str,
        stdout_path: Path,
        stderr_path: Path,
        show_console: bool = True,
    ):
        self.stage = stage
        self.step_name = step_name
        self.stdout_path = stdout_path
        self.stderr_path = stderr_path
        self.show_console = show_console

        self._stdout_lines: List[str] = []
        self._stderr_lines: List[str] = []

        self._stdout_file: TextIO | None = None
        self._stderr_file: TextIO | None = None

    def __enter__(self) -> "StepLogWriter":
        self.stdout_path.parent.mkdir(parents=True, exist_ok=True)
        self.stderr_path.parent.mkdir(parents=True, exist_ok=True)
        self._stdout_file = self.stdout_path.open("w", encoding="utf-8")
        self._stderr_file = self.stderr_path.open("w", encoding="utf-8")
        return self

    def __exit__(self, exception_type, exception, traceback) -> None:
        if self._stdout_file is not None:
            self._stdout_file.close()
            self._stdout_file = None
        if self._stderr_file is not None:
            self._stderr_file.close()
            self._stderr_file = None

    def write_stdout(self, line: str) -> None:
        self._require_open()
        self._stdout_lines.append(line)

        assert self._stdout_file is not None

        self._stdout_file.write(line)
        self._stdout_file.flush()

        if self.show_console:
            self._print_console(
                stream_name="stdout",
                text=line,
                output_stream=sys.stdout,
            )

    def write_stderr(self, line: str) -> None:
        self._require_open()
        self._stderr_lines.append(line)

        assert self._stderr_file is not None

        self._stderr_file.write(line)
        self._stderr_file.flush()

        if self.show_console:
            self._print_console(
                stream_name="stderr",
                text=line,
                output_stream=sys.stderr,
            )

    @property
    def stdout(self) -> str:
        return "".join(self._stdout_lines)

    @property
    def stderr(self) -> str:
        return "".join(self._stderr_lines)

    def _print_console(self, stream_name: str, text: str, output_stream: TextIO) -> None:
        prefix = f"[{self.stage}]" f"[{self.step_name}]" f"[{stream_name}] "

        print(
            f"{prefix}{text}",
            end="",
            file=output_stream,
            flush=True,
        )

    def _require_open(self) -> None:
        if self._stdout_file is None or self._stderr_file is None:
            raise RuntimeError("StepLogWriter must be used inside a with statement.")


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

    def create_step_log_writer(
        self,
        run_dir: Path,
        stage: str,
        step_name: str,
        attempt: int,
        show_console: bool,
    ) -> StepLogWriter:
        stdout_path, stderr_path = self._build_step_log_paths(
            run_dir=run_dir, stage=stage, step_name=step_name, attempt=attempt
        )

        return StepLogWriter(
            stage=stage,
            step_name=(f"{step_name}" f"[attempt={attempt}]"),
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            show_console=show_console,
        )

    def save_step_stdout(self, run_dir: Path, stage: str, step_name: str, stdout: str) -> Path:
        stdout_path, _ = self._build_step_log_paths(
            run_dir=run_dir, stage=stage, step_name=step_name
        )
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text(stdout, encoding="utf-8")
        return stdout_path

    def save_step_stderr(self, run_dir: Path, stage: str, step_name: str, stderr: str) -> Path:
        _, stderr_path = self._build_step_log_paths(
            run_dir=run_dir, stage=stage, step_name=step_name
        )
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path.write_text(stderr, encoding="utf-8")
        return stderr_path

    def cleanup_validation_targets(
        self, run_dir: Path, rules: list[ArtifactValidationRule]
    ) -> None:
        run_dir = Path(run_dir).resolve()

        for rule in rules:
            if not rule.required:
                continue

            path = Path(rule.path)

            if not path.is_absolute():
                path = run_dir / path

            path = path.resolve()

            # Safety boundary:
            # cleanup can only touch files/directories inside run_dir
            try:
                path.relative_to(run_dir)
            except ValueError:
                continue

            if not path.exists():
                continue

            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    def _build_step_log_paths(
        self, run_dir: Path, stage: str, step_name: str, attempt: int
    ) -> tuple[Path, Path]:
        stage_dir = run_dir / self._sanitize_name(stage)
        stage_dir.mkdir(parents=True, exist_ok=True)

        safe_step_name = self._sanitize_name(step_name)
        stdout_path = stage_dir / f"{safe_step_name}" / f"attempt_{attempt}.stdout.log"
        stderr_path = stage_dir / f"{safe_step_name}" / f"attempt_{attempt}.stderr.log"
        return stdout_path, stderr_path

    @staticmethod
    def _sanitize_name(name: str) -> str:
        sanitized = re.sub(
            r"[^A-Za-z0-9_.-]+",
            "_",
            name,
        )
        return sanitized.strip("_") or "unnamed"
