from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from typing import Any

EXPRESSION = re.compile(r"\$\{\{\s*([^{}]*?)\s*\}\}")
UNRESOLVED = re.compile(r"\$\{\{")
NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
FULL = re.compile(r"^\$\{\{\s*([^{}]*?)\s*\}\}$")


class VariableResolutionError(ValueError):
    """Invalid expression, undefined variable, or invalid resolved type."""


class StaticVariableResolver:

    def __init__(self, variables: Mapping[str, Any], run_dir: str | Path):
        """
        驗證變數名稱、型別及禁止遞迴引用
        """
        if not isinstance(variables, Mapping):
            raise VariableResolutionError("variables must be a mapping")

        self.values: dict[str, Any] = {}

        for name, value in variables.items():

            if not isinstance(name, str) or not NAME.fullmatch(name):
                raise VariableResolutionError(f"invalid variable name: {name!r}")

            if type(value) not in (str, int, float, bool):
                raise VariableResolutionError(f"unsupported type for vars.{name}")

            if isinstance(value, str) and UNRESOLVED.search(value):
                raise VariableResolutionError(f"recursive variable not supported: vars.{name}")

            self.values[name] = value

        self.run_dir = str(Path(run_dir).resolve())

    def _lookup(self, expression: str) -> Any:
        """
        查找 vars.* 或 run.dir
        """

        if expression == "run.dir":
            return self.run_dir

        if expression.startswith("vars."):
            name = expression[5:]

            if not NAME.fullmatch(name):
                raise VariableResolutionError(f"invalid expression: {expression!r}")

            if name not in self.values:
                raise VariableResolutionError(f"undefined variable: vars.{name}")

            return self.values[name]

        raise VariableResolutionError(f"unsupported expression: {expression!r}")

    def resolve(self, value: Any) -> Any:
        """
        解析單一值，完整引用時保留原型別
        """

        if not isinstance(value, str):
            return value

        full = FULL.fullmatch(value)

        if full:
            return self._lookup(full.group(1).strip())

        rendered = EXPRESSION.sub(lambda m: str(self._lookup(m.group(1).strip())), value)

        if UNRESOLVED.search(rendered):
            raise VariableResolutionError(f"malformed or unresolved expression: {rendered!r}")

        return rendered

    def string(self, value: Any, field_name: str) -> str:
        """
        要求解析結果是字串
        """

        result = self.resolve(value)

        if not isinstance(result, str):
            raise VariableResolutionError(f"{field_name} must resolve to a string")

        return result

    def timeout(self, value: Any, field_name: str = "timeout_second") -> int | float:
        """
        要求結果是有限的正整數或正浮點數
        """

        result = self.resolve(value)

        if (
            type(result) not in (int, float)
            or result <= 0
            or (type(result) is float and not math.isfinite(result))
        ):
            raise VariableResolutionError(f"{field_name} must resolve to a finite positive number")

        return result

    def resolve_dataclass(self, obj: Any, *, path: str = "config") -> Any:
        """Resolve ONLY explicit allowlisted fields, preserving immutable model types.

        Apply to LifecycleConfig and ArtifactValidationConfig (not entire RunnerConfig).


        只解析允許的 Config 欄位，產生新 dataclasss
        """

        if not is_dataclass(obj) or isinstance(obj, type):
            raise TypeError("expected a dataclass instance")

        cls_name = type(obj).__name__

        if cls_name == "LifecycleStepContent":
            return replace(
                obj,
                command=self.string(obj.command, f"{path}.command"),
                timeout_second=self.timeout(
                    obj.timeout_second,
                    f"{path}.timeout_second",
                ),
            )

        if cls_name == "ArtifactValidationRule":
            return replace(
                obj,
                path=self.string(obj.path, f"{path}.path"),
            )

        if cls_name not in (
            "LifecycleConfig",
            "LifecycleSteps",
            "ArtifactValidationConfig",
        ):
            raise TypeError(f"unsupported dataclass: {cls_name}")

        updates = {}

        for f in fields(obj):

            v = getattr(obj, f.name)

            if is_dataclass(v):
                updates[f.name] = self.resolve_dataclass(v, path=f"{path}.{f.name}")

            elif isinstance(v, list) and all(is_dataclass(x) for x in v):
                updates[f.name] = [
                    self.resolve_dataclass(x, path=f"{path}.{f.name}[{i}]") for i, x in enumerate(v)
                ]

        return replace(obj, **updates)
