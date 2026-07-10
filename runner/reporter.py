import json
import os
from dataclasses import asdict

from runner.models import RunResult


class JsonReporter:
    def save(self, result: RunResult, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "result.json")

        with open(output_path, "w") as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)
        return output_path
