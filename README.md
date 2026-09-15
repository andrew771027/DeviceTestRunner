<p align="center">
  <img src="site/images/social-preview.jpg" alt="Device Test Runner" width="100%">
</p>

# Device Test Runner

Device Test Runner 使用 YAML 定義裝置測試流程，執行既有的 Bash、Python、ADB 等命令，並保存每次執行的輸出與 JSON 報告。它負責安排測試步驟、驗證輸出檔案，以及依設定重試失敗步驟；裝置操作仍由你的腳本處理。

目前版本為 **v1.6.0**，支援五階段測試流程、步驟逾時、選擇性重試、必要與選用的輸出檔案驗證，以及 Python API 取消。Recorder 管理與遠端執行仍在規劃中。

## 安裝

需要 Python 3.10+ 與 Poetry 2.x。在專案目錄執行：

```bash
git clone git@github.com:andrew771027/DeviceTestRunner.git
cd DeviceTestRunner
poetry install
```

Poetry 會建立虛擬環境，依 `poetry.lock` 安裝專案與開發依賴。後續指令都透過 `poetry run` 執行。

## 執行測試流程

```bash
poetry run python main.py --config configs/sample.yaml
```

範例設定會示範失敗情境。2026-09-12 的本機驗證結果為 `FAILED`：`run_unstable_command` 失敗後未重試，下一步被跳過，另有五項必要檔案驗證失敗。完整紀錄見 [v1.6.0 完成條件](docs/definition_of_done/definition_of_done_v1.6.0.md)。

每次執行會建立獨立的輸出目錄，保存 `result.json` 與各次嘗試的 stdout、stderr。請讀取報告中的 `summary.status` 判斷結果：`PASSED`、`FAILED` 或 `CANCELLED`。

## 常用詞彙

| 詞彙 | 意義 |
| --- | --- |
| Run | 一次完整的測試流程 |
| Stage | 流程中的階段，例如 `setup` 或 `scenario` |
| Step | 階段中設定的一個命令步驟 |
| Attempt | 步驟的一次執行；重試會建立新的 attempt |
| Artifact | 測試產生的檔案，例如 log、CSV 或 JSON |
| Cleanup | 清理作業，包括 `teardown` 與 `global_teardown` |

## 測試生命週期

測試依序執行五個階段：

```text
global_setup
    ↓
setup
    ↓
scenario
    ↓
teardown
    ↓
global_teardown
```

各階段用途：

| Stage             | Responsibility        |
| ----------------- | --------------------- |
| `global_setup`    | 整次測試執行前的一次性環境準備       |
| `setup`           | Test case 執行前的裝置與環境設定 |
| `scenario`        | 執行主要測試內容              |
| `teardown`        | 清理單一 test case 產生的狀態  |
| `global_teardown` | 整次測試執行完成後的最終清理        |

階段失敗時，Runner 依下列規則路由：

| 失敗位置 | 後續行為 |
| --- | --- |
| `global_setup` | 停止當前 stage，跳過 `setup`、`scenario` 與 `teardown`，仍執行 `global_teardown` |
| `setup` | 停止當前 stage，跳過 `scenario`，仍執行 `teardown` 與 `global_teardown` |
| `scenario` | 停止當前 stage 的剩餘 steps，仍執行 `teardown` 與 `global_teardown` |
| `teardown` | 記錄失敗但繼續執行該 stage 的剩餘 steps，之後執行 `global_teardown` |
| `global_teardown` | 記錄失敗但繼續執行該 stage 的剩餘 steps |

上述為一般失敗路由。v1.6.0 進入 setup 區塊後，即使 setup／scenario 取消，仍執行兩個 cleanup stages；run 開始前或 global_setup 取消時只執行 global_teardown。如果 global_setup 成功後、進入 setup 區塊前已觀察到取消，也會跳過 teardown。Cleanup attempt 使用新的 token；這些是受控流程的 best effort，不涵蓋未處理 Python exception 或 KeyboardInterrupt。

最終 `summary.status` 以 `CANCELLED` 優先；沒有取消時，failed step、skipped step 或 required artifact failure 任一存在即為 `FAILED`，其餘為 `PASSED`。

## 設定測試流程

以下設定示範裝置命令、重試與 CSV 驗證：

```yaml
test_case:
  id: power_idle_test
  name: Power Idle Test
  description: Measure device power consumption during idle state.

device:
  serial: ABC123
  product: pixel
  build: build_12345

retry:
  max_attempts: 3
  delay_seconds: 1
  retry_on:
    - timeout
    - device_offline
    - artifact_missing

lifecycle:
  global_setup:
    steps:
      - name: check_environment
        type: command
        command: echo "Check environment"
        timeout_second: 30

  setup:
    steps:
      - name: check_device
        type: command
        command: adb -s ABC123 get-state
        timeout_second: 30

  scenario:
    steps:
      - name: run_idle_scenario
        type: command
        command: |
          printf "timestamp,power\n1,110\n" > result.csv
        timeout_second: 300

  teardown:
    steps:
      - name: restore_device
        type: command
        command: adb -s ABC123 shell input keyevent HOME
        timeout_second: 30

  global_teardown:
    steps:
      - name: finalize
        type: command
        command: echo "Finalize test run"
        timeout_second: 30

artifact:
  output_dir: artifacts
  validation:
    rules:
      - name: check_result_exists
        type: exists
        path: result.csv

      - name: check_result_content
        type: csv_content
        path: result.csv
        after_step: run_idle_scenario
        required: true
        required_columns:
          - timestamp
          - power
        min_rows: 1
```

`after_step` 將 validation rule 綁定到指定 step，runner 會在該 step 每次 command 成功後立即驗證。`required` 預設為 `true`：required rule 失敗會使 attempt 失敗，且只有 failure type 出現在 `retry.retry_on`、尚未達 `max_attempts` 時才重試；`required: false` 的失敗仍寫入 report，但不影響 step 或 run 狀態。Lifecycle 結束後會再次對所有規則執行 final validation，包括有 `after_step` 的規則。YAML 未設定 `retry_on` 時預設為空清單，因此不重試；`none`、`cancelled` 與未知值會被拒絕。直接使用 Python `RetryConfig()` 的預設清單不同，詳見 v1.6.0 Architecture。

## 透過 Python API 取消

取消由呼叫端持有 token 並呼叫 `cancel()`；`main.py` 尚未將 Ctrl+C／SIGTERM 轉為 token cancellation。以下示範沿用載入的 configuration，在兩秒後提出取消請求：

```python
from pathlib import Path
from threading import Timer

from runner.artifact import ArtifactManager
from runner.artifact_validator import ArtifactValidator
from runner.cancellation import CancellationToken
from runner.config import ConfigLoader
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner

config = ConfigLoader().load("configs/sample.yaml")
classifier = FailureClassifier()
runner = DeviceTestRunner(
    executor=SubprocessExecutor(Path.cwd(), classifier),
    artifact_manager=ArtifactManager(config.artifact.output_dir),
    artifact_validator=ArtifactValidator(),
    failure_classifier=classifier,
    reporter=JsonReporter(),
    show_console_output=False,
)
token = CancellationToken()
timer = Timer(2.0, token.cancel)
timer.start()
try:
    result = runner.run(config, cancellation_token=token)
    print(result.summary.status)
finally:
    timer.cancel()
    timer.join()
```

Executor 以 0.1 秒 polling 檢查取消與 timeout，對直接子程序 terminate、等待兩秒後必要時 kill。尚未處理整棵 process tree，後代程序持有 stdout／stderr pipe 時，完成時間可能延長；上述 timer 不是兩秒內返回的保證。Cancelled attempt 不做 attempt validation 或 retry，但 run 最後仍驗證所有 artifacts。

升級至 v1.6.0 時，Python 呼叫端需調整 `SubprocessExecutor.execute(..., cancellation_token=...)`，以及手動建構 result dataclasses 時的新欄位。`run(config)` 仍可不傳 token。完整差異見 [Architecture](docs/architecture/architecture_v1.6.0.md)。

## 輸出檔案

每次測試執行會建立獨立的 run directory。

範例：

```text
artifacts/
└── power_idle_test_20260722_223000/
    ├── result.json
    ├── global_setup/
    │   └── check_environment/
    │       ├── attempt_1.stdout.log
    │       └── attempt_1.stderr.log
    ├── scenario/
    │   └── run_idle_scenario/
    │       ├── attempt_1.stdout.log
    │       ├── attempt_1.stderr.log
    │       ├── attempt_2.stdout.log
    │       └── attempt_2.stderr.log
    └── result.csv
```

`result.json` 包含：

* Test case metadata
* Device metadata
* Start time
* End time
* Total duration
* Final status
* Lifecycle stage results
* Step results
* stdout and stderr artifact paths
* Validation results
* Retry information
* Per-attempt failure type, `timed_out` and `cancelled`
* Metadata `cancel_requested` and summary `cancelled_steps`

相對路徑的 artifact validation rule 會以該次 run directory 為基準解析。每一次 retry 都有獨立的 stdout／stderr log，避免後一次 attempt 覆蓋先前的診斷資訊。

## 報告範例

以下是單一步驟、無 artifact rules 的示意資料，並非 sample.yaml 的實際執行報告。

```json
{
  "metadata": {
    "test_case_id": "example_001",
    "test_case_name": "Example",
    "test_case_description": "Print one line.",
    "device_serial": "demo",
    "device_product": "demo",
    "device_build": "demo",
    "runner_version": "1.6.0",
    "started_at": "2026-09-12T00:00:00+00:00",
    "finished_at": "2026-09-12T00:00:01+00:00",
    "cancel_requested": false
  },
  "summary": {
    "status": "PASSED",
    "configured_steps": 1,
    "executed_steps": 1,
    "passed_steps": 1,
    "failed_steps": 0,
    "cancelled_steps": 0,
    "skipped_steps": 0,
    "configured_artifact_rules": 0,
    "passed_artifact_rules": 0,
    "failed_artifact_rules": 0,
    "failed_required_artifact_rules": 0,
    "duration_seconds": 1.0
  },
  "step_results": [
    {
      "stage": "scenario",
      "name": "hello",
      "command": "echo hello",
      "attempts": 1,
      "success": true,
      "cancelled": false,
      "attempt_results": [
        {
          "attempt": 1,
          "success": true,
          "failure_type": "none",
          "timed_out": false,
          "cancelled": false,
          "exit_code": 0,
          "duration_seconds": 0.1,
          "stdout": "hello\n",
          "stderr": "",
          "stdout_log_path": "artifacts/example/scenario/hello/attempt_1.stdout.log",
          "stderr_log_path": "artifacts/example/scenario/hello/attempt_1.stderr.log",
          "error": null,
          "artifact_validation_results": []
        }
      ],
      "duration_seconds": 0.2
    }
  ],
  "artifact_dir": "artifacts/example",
  "artifact_validation_results": []
}
```

結果消費端應以 `summary.status` 判斷 run；`RunResult.passed` 目前只檢查 step success，無法完整反映取消請求或 final artifact failure。`StepAttemptResult.passed` 也只檢查 exit code，請使用 `success` 與 failure flags。

## 架構

```text
YAML Configuration
        ↓
Config Loader
        ↓
RunnerConfig
        ↓
DeviceTestRunner
        ├── Lifecycle Orchestration
        ├── CancellationToken
        ├── RetryPolicy
        ├── SubprocessExecutor
        ├── ArtifactManager
        ├── ArtifactValidator
        └── JsonReporter
                ↓
       result.json / per-attempt logs / validation results
```

Device Test Runner 的核心資料流：

```text
Config
  ↓
Runner
  ↓
Executor
  ↓
StepResult
  ↓
ArtifactManager
        ↓
RunResult / result.json
```

## 執行專案測試

執行所有測試：

```bash
poetry run pytest
```

顯示較完整輸出：

```bash
poetry run pytest -v
```

只執行 retry 相關測試：

```bash
poetry run pytest -m retry
```

只執行 cancellation 標記測試（不等同完整 suite）：

```bash
poetry run pytest -m cancelled
```

只執行 artifact 相關測試：

```bash
poetry run pytest -m artifact
```

歷史驗證紀錄（2026-09-12，Python 3.14）：`.venv/bin/python -m pytest -q` → **153 passed in 39.39s**。150 個測試函式皆有 Given／When／Then 說明；參數化後共 153 個案例。

## 持續整合

[CI workflow](.github/workflows/ci.yml) 會在 push 至 `main` 或建立以 `main` 為目標的 pull request 時執行。流程安裝 Python、Poetry 與專案依賴後，執行 pytest。

在本機執行相同的測試：

```bash
poetry install
poetry run pytest
```

## 手動更新版本文件

`.github/workflows/manual.yml` 的 `workflow_dispatch` 接受 `release_version`（如 `1.6.0`，不含 v）、`target_branch`（實際 checkout 與 push 的既有分支）及 `model`。GitHub Actions 的 Use workflow from 選項決定讀取哪個分支的 workflow 定義。

流程先安裝專案、跑 baseline tests，再請 Codex 更新文件與測試說明；驗證 `pytest -q`、`git diff --check` 與 Given／When／Then 行數後，有變更才 commit 並直接 push 到目標分支。這個流程不建立 PR、tag 或 GitHub Release。

Repository secret 名稱為 `OPENAI_API_KEY`，在 CLI invocation 映射成 `CODEX_API_KEY`；`--approve-for-me` 與 `--sandbox` 不同時使用。目標分支需允許這次 push，API 帳戶需有可用額度及模型存取權。

## 開發與版本規劃

目前先補齊單機執行與取消流程，再加入可重用設定與 recorder 管理：

1. v1.6.1：程序群組終止、輸出串流收尾與 CLI 取消訊號。
2. v1.6.2：整次 run 的逾時設定。
3. v1.6.3：取消後的清理範圍、時間限制與部分結果保存。
4. v1.7.0～v1.7.2：YAML 靜態變數、環境變數與執行資訊。
5. v1.8 之後：recorder、hooks、執行摘要、批次與並行執行。
6. v2.0：controller／worker 遠端執行。

詳細範圍與 keyword-driven 設計見 [Roadmap](docs/roadmap.md)。歷史變更見 [CHANGELOG](CHANGELOG.md)。提交與發佈前請使用 [提交檢查清單](CommitManual.md)。

## 文件

| 文件 | 用途 |
| --- | --- |
| [架構 v1.6.0](docs/architecture/architecture_v1.6.0.md) | 元件、取消路由、報告欄位與相容性 |
| [測試矩陣 v1.6.0](docs/test_matrix/test_matrix_v1.6.0.md) | 功能對應的測試與覆蓋限制 |
| [驗收條件 v1.6.0](docs/acceptance_criteria/acceptance_criteria_v1.6.0.md) | 可觀察的預期行為 |
| [完成條件 v1.6.0](docs/definition_of_done/definition_of_done_v1.6.0.md) | 驗證紀錄與待完成的發佈項目 |

`docs/` 內的舊版文件保留當時的設計與介面，使用時請確認版本。
