"""解析執行前的靜態變數，僅支援 vars.NAME 與 run.dir。

ConfigLoader 驗證定義並保留模板；Runner 建立 run directory 後再解析允許的
欄位。解析器不執行 expression、不讀取 environment，也不進行 shell escaping。
"""

import math
import re
import os
from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from typing import Any

# 比對字串內的 ${{ ... }} 模板，可用於多個引用的內插。
# \s* 允許前後空白；([^{}]*?) 非貪婪擷取不含大括號的內容至 group(1)。
# 例："out/${{ vars.name }}.txt" → group(1) 為 "vars.name"。
# 此處僅辨識模板結構，引用內容是否合法由 _lookup 驗證。
EXPRESSION = re.compile(r"\$\{\{\s*([^{}]*?)\s*\}\}")

# 搜尋模板起始符號，即使缺少結尾也能偵測，用於拒絕遞迴或未解析的引用。
# 例："${{ vars.name"、"out/${{ vars.name }}" 均可被 search 找到。
UNRESOLVED = re.compile(r"\$\{\{")

# 變數名稱：首字元為 ASCII 英文字母或底線，後續可加數字；以 fullmatch 驗證。
# 例："device_1"、"_timeout" 合法；"1device"、"device-name" 不合法。
NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# 與 EXPRESSION 相同的模板結構，加上 ^ / $ 標示頭尾，並以 fullmatch 比對整串。
# 完整引用保留原始 scalar 型別；例：vars.timeout = 30 時，
# "${{ vars.timeout }}" 解析為整數 30；"timeout=${{ vars.timeout }}" 不符合 FULL。
FULL = re.compile(r"^\$\{\{\s*([^{}]*?)\s*\}\}$")


class VariableResolutionError(ValueError):
    """變數定義、引用語法或解析後的欄位型別不合法。"""


class StaticVariableResolver:
    """保存變數的副本，並以當次 run 的絕對路徑解析設定。

    僅 command、timeout_second 與 validation path 由 resolve_dataclass 處理。
    原始 frozen dataclass 不會被修改，因此同一份設定可用於多次 run。
    """

    def __init__(self, variables: Mapping[str, Any], run_dir: str | Path, environ: Mapping[str, str] | None = None):
        """驗證並複製變數定義，將 run_dir 正規化為絕對路徑。

        Args:
            variables: 名稱須符合 NAME，值限 str、int、float 或 bool。
                字串不得含模板起始符號，避免變數間遞迴引用。
            run_dir: 當次 run 的目錄；此處不建立目錄。

        Raises:
            VariableResolutionError: 定義不是 mapping，或名稱／值不合法。
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

        # Snapshot the environment once, so one run has consistent values.
        self.environ = dict(os.environ if environ is None else environ)

    def _lookup(self, expression: str) -> Any:
        """查找單一白名單引用；不支援運算、巢狀欄位或 env namespace。

        run.dir 回傳絕對路徑字串；vars.NAME 回傳宣告時的原始值。
        未定義名稱或不支援的語法會拋出 VariableResolutionError。
        """

        if expression.startswith("env."):
            name = expression[4:]
            if not NAME.fullmatch(name):
                raise VariableResolutionError(f"invalid environment variable name: {name!r}")

            if name not in self.environ:
                raise VariableResolutionError(f"undefined environment variable: env. {name}")
            
            return environ[name]

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
        """解析單一值，完整引用保留型別，字串內插則轉為 str。

        非字串原樣回傳。完整引用如 ${{ vars.duration }} 可回傳 int 或 float；
        內插如 "duration=${{ vars.duration }}" 始終回傳字串。
        替換後若仍含模板起始符號，視為不完整或未解析的引用並拋出錯誤。
        此方法不驗證使用欄位的型別；呼叫端應使用 string 或 timeout。
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
        """解析 command 或 path，要求結果為字串。

        不將完整引用的數字或 bool 隱式轉成字串；field_name 用於錯誤定位。
        """

        result = self.resolve(value)

        if not isinstance(result, str):
            raise VariableResolutionError(f"{field_name} must resolve to a string")

        return result

    def timeout(self, value: Any, field_name: str = "timeout_second") -> int | float:
        """解析每次 attempt 的 timeout 秒數，保留 int 或 float 型別。

        拒絕字串、bool、零、負數、NaN 與 infinity。使用精確型別檢查，
        避免 bool 因為是 int 的子類別而被當成合法秒數。
        field_name 可包含 stage 和索引，方便定位無效的設定。
        """

        result = self.resolve(value)

        invalid_number = type(result) not in (int, float) or result <= 0
        if invalid_number or (type(result) is float and not math.isfinite(result)):
            raise VariableResolutionError(f"{field_name} must resolve to a finite positive number")

        return result

    def resolve_dataclass(self, obj: Any, *, path: str = "config") -> Any:
        """解析允許的 dataclass 欄位，回傳同型別的新物件。

        LifecycleStepContent 解析 command 與 timeout_second；
        ArtifactValidationRule 只解析 path，其餘驗證參數維持原值。
        容器限 LifecycleConfig、LifecycleSteps、ArtifactValidationConfig；
        RunnerConfig 與 artifact.output_dir 不在解析範圍內。

        Args:
            obj: 支援的 dataclass instance，不接受 dataclass class。
            path: 錯誤訊息的欄位前綴，遞迴時附加欄位名稱與 list 索引。

        Raises:
            TypeError: 輸入不是 instance，或 dataclass 不在白名單內。
            VariableResolutionError: 引用無效，或解析後不符合欄位型別。
        """

        if not is_dataclass(obj) or isinstance(obj, type):
            raise TypeError("expected a dataclass instance")

        cls_name = type(obj).__name__

        if cls_name == "DeviceInfo":
            return replace(obj, serial=self.string(obj.serial, f"{path}.serial"))

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
