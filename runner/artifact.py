import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from typing import TextIO

class StepLogWriter:
    """ 負責單一 step 的 stdout/stderr。 
    每收到一行輸出時：
    1. 寫入 log file 
    2. flush log file 
    3. 顯示到 terminal 
    4. 保存到 memory，最後建立 StepResult 
    """

    def __init__(self, stage: str, step_name: str, stdout_path: Path, stderr_path: Path, show_console: bool = True):
        self.stage = stage
        self.step_name = step_name
        self.stdout_path = stdout_path
        self.stderr_path = stderr_path
        self.show_console = show_console 

        self._stdout_lines:List[str] = []
        self._stderr_lines:List[str] = []

        self._stdout_file: TextIO | None = None
        self._stderr_file: TextIO | None = None
    
    def __enter__(self) -> "StepLogWriter":
        self._stdout_file = self.stdout_path.open("w", encoding="utf-8")
        self._stderr_file = self.stderr_path.open("w", encoding="utf-8")
        return self
    
    def __exit__(self, exception_type, exception, traceback) -> None:
        if self.stdout_file not None:
            self.stdout_file.close()
        if self.stderr_file not None:
            self.stderr_file.close()
    
    def write_stdout(self, line: str) -> None:
        self._require_open()
        self._stdout_lines.append(line)

        assert self._stdout_file is not None

        self._stdout_file.write_text(line)
        self._stdout_file.flash(line)

        if self.show_console:
            self._print_console(
                stream_name="stdout",
                text=line,
                output_stream=sys.stdout,
            )

    def write_stderr(self, line: str) -> None:
        self._require_open()
        self._stdout_lines.append(line)

        assert self._stderr_file is not None

        self._stderr_file.write_text(line)
        self._stderr_file.flash()

        if self.show_console:
            self._print_console(
                stream_name="stderr",
                text=line,
                output_stream=sys.stderr
            )
    
    @property
    def stdout(self) -> str:
        return "".join(self.stdout_lines)

    @property
    def stderr(self) -> str:
        return "".join(self.stdeff_lines)
    
    def _print_console(self, stream_name:str, text:str, output_stream: TextIO) -> None:

        prefix = (f"[{self.stage}]"
                  f"[{self.step_name}]"
                  f"[{self.stream_name}] "    
                  )
        
        print(f"{prefix}{text}", 
              end="",
              file=output_stream,
              flush=True,
            )
    
    def _require_open(self) -> None:
        if (self._stdout_file is None or self._stderr_file is None):
            raise RuntimeError("StepLogWriter must be used inside " 
                               "a with statement.")

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

    def create_step_log_writer(self, run_dir: Path, stage: str, step_name: str, show_console: bool) -> StepLogWriter:
        stage_dir = run_dir / self._sanitize_name(stage)

        safe_step_name = self._sanitize_name(step_name)

        stdout_path = stage_dir / f"{safe_step_name}.stdout.log"

        stderr_path = stage_dir / f"{safe_step_name}.stderr.log"

        return StepLogWriter(
            stage=stage,
            step_name=step_name,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            show_console=show_console
        )


#    def save_step_stdout(self, run_dir: Path, stage: str, step_name: str, stdout: str) -> Path:
#        stage_dir = run_dir / self._sanitize_name(stage)
#
#        stage_dir.mkdir(parents=True, exist_ok=True)
#
#        safe_step_name = self._sanitize_name(step_name)
#
#        output_path = stage_dir / f"{safe_step_name}.stdout.log"
#
#        output_path.write_text(stdout, encoding="utf-8")
#
#        return output_path
#
#    def save_step_stderr(self, run_dir: Path, stage: str, step_name: str, stderr: str) -> Path:
#        stage_dir = run_dir / self._sanitize_name(stage)
#
#        stage_dir.mkdir(parents=True, exist_ok=True)
#
#        safe_step_name = self._sanitize_name(step_name)
#
#        output_path = stage_dir / f"{safe_step_name}.stderr.log"
#
#        output_path.write_text(stderr, encoding="utf-8")
#
#        return output_path

    @staticmethod
    def _sanitize_name(name: str) -> str:

        sanitized = re.sub(
            r"[^A-Za-z0-9_.-]+",
            "_",
            name,
        )
        return sanitized.strip("_") or "unnamed"
