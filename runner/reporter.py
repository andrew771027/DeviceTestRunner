import json
from dataclasses import asdict
from pathlib import Path

from runner.models import RunResult


class JsonReporter:
    def save(self, result: RunResult, output_dir: str) -> None:
        output_path = Path(output_dir) / "result.json"

        output_path.write_text(
            json.dumps(
                asdict(result),
                indent=4,
            )
        )
