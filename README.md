# Device Test Runner

Device Test Runner 是一個針對 **Device Validation Domain** 設計的測試流程執行器。

它負責載入測試設定、執行測試生命週期、控制外部 commands 或 scripts、保存執行結果與 artifacts，並逐步延伸至 artifact validation、retry、timeout、recorder lifecycle，以及未來的 controller／worker 架構。

Device Test Runner 的定位不是取代既有的硬體測試腳本，而是在既有工具之上提供一層統一的 **orchestration layer**。

---

## Overview

在 Device Validation Lab 中，一個測試流程通常包含：

1. 準備裝置與環境
2. Flash device build
3. 啟動 recorder
4. 執行 test scenario
5. 停止 recorder
6. 收集測試輸出
7. 驗證 artifacts
8. 產生測試報告
9. 清理測試環境

這些流程可能由不同的 Bash、Python、ADB、Fastboot、Appium 或其他工具完成。

Device Test Runner 將這些既有工具組合成一致的測試生命週期，並統一管理：

* Execution order
* Step status
* Timeout
* Retry
* stdout
* stderr
* Artifacts
* Validation
* Cleanup
* Execution summary

---

## Project Goals

Device Test Runner 的主要目標包括：

* 使用 YAML 定義 device test scenario
* 將 runner 與 domain scripts 分離
* 支援完整 test lifecycle
* 使用 subprocess 執行既有 scripts 和 commands
* 統一管理 stdout、stderr、report 和 measurement artifacts
* 即使測試失敗，也能正確執行 teardown
* 提供 artifact validation
* 支援 recorder 與 scenario 的協作
* 建立可追蹤的 execution report
* 未來支援 remote worker 與 controller／worker 架構
* 未來支援 keyword-driven test definition

---

## Design Principles

### Orchestration over Domain Logic

Device Test Runner 負責測試流程控制，不負責所有硬體測試細節。

例如：

* Flash script 負責實際刷機
* Recorder 負責實際量測
* Scenario script 負責操作裝置
* Parser 負責解析量測結果
* Device Test Runner 負責安排執行順序、處理錯誤並保存結果

### Configuration-Driven

測試流程透過 YAML configuration 定義，避免將每個 test case 寫死在 runner 裡。

### Artifact-First

每次測試執行都應保留足夠資訊，讓失敗可以被追蹤與重現。

### Failure-Aware Lifecycle

即使 setup 或 scenario 失敗，teardown、recorder stop 和 artifact finalization 仍應盡可能執行。

### Incremental Evolution

專案先建立可靠的單機 runner，再逐步延伸到 remote execution 和 distributed architecture。

---

## Current Architecture

```text
YAML Configuration
        ↓
Config Loader
        ↓
RunnerConfig
        ↓
DeviceTestRunner
        ↓
Lifecycle Orchestration
        ↓
CommandStepExecutor
        ↓
subprocess
        ↓
ArtifactManager
        ↓
report.json / stdout / stderr / artifacts
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
RunResult / report.json
```

詳細架構說明請參考：

* [Architecture](docs/architecture.md)
* [Roadmap](docs/roadmap.md)

---

## Test Lifecycle

目前 Device Test Runner 使用以下生命週期：

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

未來 recorder lifecycle 會與 scenario 協作：

```text
start recorder
    ↓
wait until recorder is ready
    ↓
execute scenario
    ↓
stop recorder
    ↓
collect recorder artifacts
```

---

## Project Structure

```text
device-test-runner/
├── README.md
├── CHANGELOG.md
├── pyproject.toml
├── configs/
│   └── sample_device_test.yaml
├── docs/
│   ├── architecture.md
│   └── roadmap.md
├── src/
│   └── device_test_runner/
│       ├── __init__.py
│       ├── artifact.py
│       ├── config_loader.py
│       ├── executor.py
│       ├── models.py
│       └── runner.py
└── tests/
    ├── unit/
    └── integration/
```

實際目錄可能隨版本演進調整。

---

## Configuration Example

以下是一個簡化的 YAML configuration：

```yaml
test_case:
  id: power_idle_test
  name: Power Idle Test
  description: Measure device power consumption during idle state.

device:
  serial: ABC123
  product: pixel
  build: build_12345

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
        command: python3 scripts/run_idle_scenario.py
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
```

---

## Requirements

目前專案主要使用：

* Python 3.10+
* Standard library
* PyYAML
* pytest

專案刻意減少第三方 dependencies，讓核心 orchestration 邏輯保持清楚，並將學習重點放在：

* Python design
* subprocess
* process lifecycle
* test lifecycle
* artifact management
* error handling
* distributed systems

---

## Installation

Clone repository：

```bash
git clone <repository-url>
cd device-test-runner
```

建立 virtual environment：

```bash
python3 -m venv .venv
```

啟用 virtual environment。

macOS／Linux：

```bash
source .venv/bin/activate
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
```

安裝 dependencies：

```bash
pip install -e .
```

安裝 development dependencies：

```bash
pip install -e ".[dev]"
```

---

## Running the Tests

執行所有測試：

```bash
pytest
```

顯示較完整輸出：

```bash
pytest -v
```

只執行 unit tests：

```bash
pytest tests/unit
```

只執行 integration tests：

```bash
pytest tests/integration
```

---

## Running Device Test Runner

實際執行方式會依目前版本的 CLI 或 entry point 調整。

預期使用方式：

```bash
python3 -m device_test_runner configs/sample_device_test.yaml
```

未來 CLI 預計提供：

```bash
device-test-runner run configs/sample_device_test.yaml
device-test-runner validate configs/sample_device_test.yaml
device-test-runner report show artifacts/<run-id>/report.json
```

---

## Artifact Output

每次測試執行會建立獨立的 run directory。

範例：

```text
artifacts/
└── power_idle_test_20260722_223000/
    ├── report.json
    ├── stdout/
    │   ├── global_setup_check_environment.log
    │   ├── setup_check_device.log
    │   └── scenario_run_idle_scenario.log
    ├── stderr/
    │   ├── global_setup_check_environment.log
    │   ├── setup_check_device.log
    │   └── scenario_run_idle_scenario.log
    └── recorder/
        └── power.csv
```

`report.json` 預期包含：

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
* Timeout information
* Failure summary

---

## Example Report

```json
{
  "metadata": {
    "test_case_id": "power_idle_test",
    "test_case_name": "Power Idle Test",
    "device": {
      "serial": "ABC123",
      "product": "pixel",
      "build": "build_12345"
    },
    "start_time": "2026-07-22T22:30:00",
    "end_time": "2026-07-22T22:32:05"
  },
  "status": "FAILED",
  "duration_seconds": 125.0,
  "steps": [
    {
      "stage": "scenario",
      "name": "run_idle_scenario",
      "command": "python3 scripts/run_idle_scenario.py",
      "success": false,
      "exit_code": 1,
      "duration_seconds": 120.0
    }
  ]
}
```

Report schema 會隨專案版本逐步擴充。

---

## Roadmap

| Version | Topic                        | Status      |
| ------- | ---------------------------- | ----------- |
| v1.0    | Basic YAML Runner            | Completed   |
| v1.1    | Naming and Model Refactoring | Completed   |
| v1.2    | Artifact Management          | Completed   |
| v1.3    | Test Lifecycle               | In Progress |
| v1.4    | Artifact Validation          | Planned     |
| v1.5    | Retry Policy                 | Planned     |
| v1.6    | Timeout and Cancellation     | Planned     |
| v1.7    | Recorder Lifecycle           | Planned     |
| v1.8    | Hook and Teardown Guarantees | Planned     |
| v1.9    | Execution Summary            | Planned     |
| v2.0    | Controller and Worker        | Future      |

完整版本規劃請參考：

[Device Test Runner Roadmap](docs/roadmap.md)

---

## Keyword-Driven Direction

未來 Device Test Runner 將支援 Keyword-Driven 測試定義。

目標是讓較不熟悉 Python 或 Bash 的 Lab 成員，可以使用高階 domain keywords 組合測試流程。

範例：

```yaml
scenario:
  steps:
    - keyword: flash_device
      arguments:
        image: build_12345.zip

    - keyword: start_power_recorder
      arguments:
        sampling_rate: 1000

    - keyword: set_brightness
      arguments:
        level: 50

    - keyword: play_video
      arguments:
        duration_seconds: 300

    - keyword: stop_power_recorder
```

預計加入：

* KeywordRegistry
* KeywordExecutor
* KeywordDefinition
* KeywordContext
* Domain Keyword Libraries
* Keyword parameter validation
* Keyword documentation generation

YAML 仍會作為底層 scenario definition，Keyword-Driven layer 則建立在 lifecycle 與 executor 之上。

---

## Versioning

本專案預計使用 Semantic Versioning：

```text
MAJOR.MINOR.PATCH
```

例如：

```text
v1.4.0
v1.4.1
v1.5.0
v2.0.0
```

版本規則：

* `MAJOR`：重大架構變更或不相容改動
* `MINOR`：新增向下相容功能
* `PATCH`：Bug fix 或小型改善

例如：

* `v1.4.0`：加入 Artifact Validation
* `v1.4.1`：修正 file size validation
* `v1.5.0`：加入 Retry Policy
* `v2.0.0`：加入 Controller／Worker architecture

---

## Development Workflow

建議使用簡化版 GitHub Flow：

```text
main
 ├── feature/artifact-validation
 ├── feature/retry-policy
 ├── feature/recorder-lifecycle
 ├── fix/report-status
 └── docs/update-architecture
```

開發流程：

```text
Roadmap
   ↓
GitHub Milestone
   ↓
GitHub Issue
   ↓
Feature Branch
   ↓
Pull Request
   ↓
Merge to main
   ↓
Git Tag
   ↓
GitHub Release
```

Branch naming examples：

```text
feature/artifact-validation
feature/retry-policy
fix/timeout-result
test/add-lifecycle-integration-test
docs/update-roadmap
```

---

## Definition of Done

一個版本完成前，至少應滿足：

* 功能已實作
* Unit tests 通過
* Integration tests 通過
* Example YAML 可以執行
* Error handling 已確認
* Artifacts 可以被保存
* `report.json` 格式已確認
* README 或 docs 已更新
* `CHANGELOG.md` 已更新
* 對應 GitHub Issues 已關閉
* Git tag 已建立
* GitHub Release notes 已建立

---

## Current Development Focus

目前優先事項：

1. 完成 v1.3 Test Lifecycle
2. 補上歷史版本 Git tags
3. 完善 README 與 architecture 文件
4. 建立 CHANGELOG
5. 建立 GitHub Project 與 Milestones
6. 開始 v1.4 Artifact Validation
7. 逐步完成 Retry、Timeout 與 Recorder Lifecycle
8. 在單機 lifecycle 穩定後進入 Controller／Worker

目前不優先處理：

* 複雜 Web UI
* Kubernetes deployment
* 大型 message queue
* Microservices 拆分
* 多租戶權限
* 過度抽象的 plugin architecture
* 複雜 distributed scheduling

目前最重要的是建立可靠且可測試的單機 execution lifecycle。

---

## Long-Term Direction

Device Test Runner 預計從單機測試執行器逐步演化為 Device Validation Platform 的核心執行層。

```text
Existing Scripts
       ↓
Device Test Runner
       ↓
Lifecycle Orchestration
       ↓
Artifact Management
       ↓
Artifact Validation
       ↓
Recorder Coordination
       ↓
Remote Worker
       ↓
Controller
       ↓
Device Validation Platform
```

這個專案同時作為以下能力的實作練習：

* Python software design
* Test architecture
* Test lifecycle
* Orchestration
* Process management
* Artifact management
* Reliability engineering
* Distributed systems
* Developer productivity
* Test infrastructure
* Platform engineering

---

## Documentation

* [Architecture](docs/architecture.md)
* [Roadmap](docs/roadmap.md)
* [Changelog](CHANGELOG.md)

---

## Project Status

Device Test Runner 目前仍在持續開發中。

現階段專案重點是建立一個清楚、可靠、可測試的單機 Device Test Runner，並逐步加入實際 Device Validation 所需的 lifecycle、artifact、recorder 與 failure handling 能力。
