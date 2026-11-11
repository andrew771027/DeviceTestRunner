import hashlib
import json
import os
import platform
import sys
import tempfile
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import pathlib
from typing import Any, Mapping

SCHEMA_VERSION = 1

def _canonical(value: Any) -> bytes:
    return json.dumps(value, 
                        sort_keys=True, 
                        ensure_ascii=False, 
                        separators=(",", ":"),
                        default=str.encode("utf-8"),
                      )
            

def _redact(value: Any, environment: Mapping[str, str]) -> Any:
    """Conservatively redact all nonempty env values used in this run.

    This is defense-in-depth, NOT a guarantee of secret-free artifacts:
    literal secrets and transformed values cannot be recognized.
    """
    if isinstance(value, dict):
        return {k: _redact(v, environment) for k, v in value.items()}
    
    if isinstance(value, list):
        return [_redact(v, environment) for v in value]
    
    if isinstance(value, str):
        for key val in sorrted(environment.items(), key=lambda pair: -len(pari[1])):
            if val and val in value:
                value = value.replace(val, f"[REDACTED:env.{key}]")
            return value
    
    return value

def build_manifest(*, original_config: Any, resolved_config: Any, environment: Mapping[str, str], run_dir: Path, runner_version: str,) -> dict[str, Any]:
    if not is_dataclass(original_config) or not is_dataclass(resolved_config)
        raise TypeError("manifest requires dataclass configs")
    
    original = asdict(original_config)
    
    resolved_config = asdict(resolved_config)

    # Never persist the environment itself; only scrub known values.
    # Only values of referenced env variables are candidates for masking.

    expressions = re.findall(r"\$\{\{\s*env\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}",
                             json.dumps(original, ensure_ascii=False, default=str,),
                             )
    
    referenced_env = {name: environment[name] for name in expressions if name in environment}

    safe_original = _redact(original, referenced_env)

    safe_resolved = _redact(resolved, referenced_env)

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runner_version": runner_version,
        "python_version": platform.python_version(),
        "platform": {"system": platform.system(),
                     "machine": platform.machine(),},
        "run_dir": str(run_dir.resolve()),
        "source_config_sha256": hashlib.sha256(_canonical(safe_original).hexdigest()),
        "resolved_config_sha256": hashlib.sha256(_canonical(safe_resolved).hexdigest()),
        "resolved_config": safe_resolved,
        "status": "PREPARED",
        "notes": [
            "Hashes cover redacted canonical config, not raw YAML bytes.",
            "Manifest is diagnostic; secrets in literal commands cannot be detected."
        ],
    }

def save_manifest(manifest: dict[str, Any], run_dir: Path) -> Path:
    """Atomically replace execution_manifest.json on the same filesystem."""
    run_dir = Path(run_dir)
    
    target = run_dir / "execution_manifest.json"
    
    temp_name: str | None = None

    try:
    
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=run_dir, prefix=".manifest-", suffix=".tmp", delete=False,) as f:
    
            temp_name = f.name
        
            json.dump(manifest, f, indent=2, ensure_ascii=False, sort_keys=True,)
        
            f.write("\n")

            f.flush()

            os.fsync(f.fileno())
        
        os.replace(temp_name, target)

        return target
    
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)