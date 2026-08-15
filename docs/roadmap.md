# Device Test Runner Roadmap

## 1. Project Vision

Device Test Runner 是一個針對 Device Validation Domain 設計的測試流程執行器。

它的目標不是取代現有的 Google Scripts Repo、硬體量測工具或各 Lab 既有的測試腳本，而是提供一個統一的 orchestration layer，負責：

* 載入測試設定
* 執行測試生命週期
* 控制外部 command 或 script
* 管理 stdout、stderr、report 與其他 artifacts
* 驗證測試輸出
* 彙整執行結果
* 支援 recorder 與 scenario 的協作
* 未來延伸至 remote execution 與 controller／worker 架構

Device Test Runner 將盡量保持 domain script 與 runner framework 分離。

各 Lab 可以保留既有的 Bash、Python、ADB、Fastboot、Appium 或其他測試工具，並由 Device Test Runner 統一管理執行流程與結果。

---

## 2. Design Principles

### 2.1 Orchestration over Domain Logic

Device Test Runner 負責流程控制，但不應承擔所有硬體測試細節。

例如：

* Flash script 負責實際執行 Android image flashing
* Power recorder 負責實際量測與輸出資料
* Scenario script 負責操作裝置與產生測試行為
* Parser 負責解析 domain-specific measurement data
* Device Test Runner 負責安排以上元件的執行順序、狀態與 artifacts

### 2.2 Configuration-Driven

測試流程應透過 YAML 或其他 configuration definition 描述，而不是把每個 test case 寫死在 runner 裡。

### 2.3 Artifact-First

每次執行都應留下可追蹤的 artifacts，包括：

* stdout
* stderr
* report.json
* metadata
* recorder output
* measurement files
* validation results
* execution summary

### 2.4 Failure-Aware Lifecycle

即使某個步驟失敗，runner 仍需正確處理：

* teardown
* recorder stop
* process cleanup
* artifact finalization
* failure reporting

### 2.5 Incremental Evolution

專案先完成單機版 lifecycle orchestration，再逐步加入：

* validation
* retry
* timeout
* recorder lifecycle
* execution summary
* remote worker
* controller／worker
* keyword-driven test definition

---

# 3. Version Roadmap

## v1.0 — Basic YAML Runner

### Goal

建立最小可執行的 Device Test Runner。

### Core Features

* YAML configuration
* RunnerConfig model
* DeviceTestCase model
* DeviceInfo model
* Workflow definition
* CommandStepExecutor
* subprocess command execution
* StepResult
* DeviceTestRunner orchestration
* 基本 PASSED／FAILED 判定

### Learning Focus

* Configuration loading
* Data model design
* subprocess
* orchestration basics
* input／output flow

### Status

Completed

---

## v1.1 — Naming and Model Refactoring

### Goal

統一 YAML、Python models、runner 與 tests 之間的命名。

### Core Features

* 調整 model 命名
* 移除容易與 pytest collection 衝突的名稱
* 對齊 configuration schema
* 改善 module responsibilities
* 更新 unit tests
* 更新 integration tests

### Learning Focus

* Naming consistency
* Refactoring
* backward compatibility
* test maintenance

### Status

Completed

---

## v1.2 — Artifact Management

### Goal

將測試輸出集中交由 ArtifactManager 管理。

### Core Features

* ArtifactManager
* 建立每次 execution 的 run directory
* 儲存 step stdout
* 儲存 step stderr
* 產生 report.json
* 在 report.json 寫入 metadata
* 彙整 test case、device 與 execution status
* Artifact directory naming convention

### Expected Output

```text
artifacts/
└── <test-case-id>_<timestamp>/
    ├── report.json
    ├── metadata.json
    ├── stdout/
    └── stderr/
```

### Learning Focus

* Artifact ownership
* Output organization
* metadata design
* serialization
* separation of concerns

### Status

Completed

---

## v1.3 — Test Lifecycle

### Goal

從單一 workflow steps 提升為完整的 test lifecycle orchestration。

### Lifecycle Stages

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

### Core Features

* LifecycleConfig
* LifecycleSteps
* LifecycleStepContent
* stage-based execution
* stage name 寫入 StepResult
* lifecycle status aggregation
* stage execution ordering
* scenario failure handling
* teardown execution foundation
* lifecycle report structure

### Learning Focus

* Test lifecycle
* stage orchestration
* execution ordering
* state transitions
* status aggregation

### Status

Completed

---

## v1.4 — Artifact Validation

### Goal

在測試完成後，自動驗證必要 artifacts 是否正確產生。

### Core Features

* ArtifactValidator
* ArtifactValidationResult
* YAML-based validation rules
* File existence validation
* Minimum and maximum file size validation
* File extension validation
* Non-empty directory validation
* CSV columns and row count validation
* JSON path and expected value validation
* Validation result aggregation
* Validation failure 影響最終 run status
* Validation results 寫入 result.json

### Example Validation Rules

```yaml
artifact:
  output_dir: artifacts
  validation:
    rules:
      - name: check_power_file
        type: exists
        path: recorder/power.csv

      - name: check_power_file_size
        type: file_size
        path: recorder/power.csv
        min_size_bytes: 1024
```

### Expected Report

```json
{
  "validation": {
    "status": "FAILED",
    "results": [
      {
        "name": "check_power_file",
        "type": "exists",
        "path": "recorder/power.csv",
        "passed": true
      },
      {
        "name": "check_power_file_size",
        "type": "file_size",
        "path": "recorder/power.csv",
        "passed": false,
        "message": "File size is below minimum requirement"
      }
    ]
  }
}
```

### Learning Focus

* Validation abstraction
* policy separation
* domain-independent validation
* status aggregation
* post-execution verification

### Status

Completed

---

## v1.5 — Retry Policy

### Goal

針對可恢復的失敗提供可設定的 retry mechanism。

### Core Features

* RetryPolicy
* maximum attempts
* retry delay
* attempt history 寫入 StepResult
* 每次 attempt 的 stdout／stderr
* final attempt result aggregation
* retry metadata 寫入 result.json
* retry configuration validation
* 未提供 retry config 時預設只執行一次

### Example Configuration

```yaml
retry:
  max_attempts: 3
  delay_seconds: 5
```

目前所有失敗的 command attempt 都使用相同 retry policy。依 exit code 或 error category 決定是否重試，將在後續版本擴充。

### Future Error Classification

初期可區分：

* command not found
* timeout
* transient device unavailable
* adb disconnected
* script failure
* validation failure
* non-retryable configuration error

### Learning Focus

* Policy objects
* attempt tracking
* transient failure
* error classification
* idempotency

### Status

Completed

---

## v1.6 — Timeout and Cancellation

### Goal

控制 command 與 process 的最大執行時間，並能安全終止超時程序。

### Core Features

* Per-step timeout
* subprocess timeout handling
* timeout result classification
* graceful termination
* force kill fallback
* child process cleanup
* cancellation state
* timeout details 寫入 report.json
* partial stdout／stderr preservation

### Learning Focus

* Process lifecycle
* signals
* process groups
* graceful shutdown
* cleanup guarantees
* cancellation semantics

### Status

Planned

---

## v1.7 — Recorder Lifecycle

### Goal

支援 background recorder 與 foreground scenario 同時運作。

### Expected Flow

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

### Core Features

* RecorderConfig
* RecorderController
* background process start
* readiness detection
* recorder startup timeout
* recorder process state
* recorder stdout／stderr capture
* recorder stop command
* graceful recorder shutdown
* force kill fallback
* recorder artifacts collection
* recorder failure propagation

### Possible Readiness Strategies

* fixed delay
* log keyword detection
* output file creation
* health command
* process running check

### Learning Focus

* Background process
* process synchronization
* readiness
* start／stop lifecycle
* concurrent execution
* resource ownership

### Status

Planned

---

## v1.8 — Hook and Teardown Guarantees

### Goal

確保即使 setup 或 scenario 失敗，必要的 cleanup 仍會執行。

### Core Features

* always-run teardown
* always-run global teardown
* cleanup hooks
* failure hook
* post-step hook
* lifecycle interruption handling
* multiple failure preservation
* primary failure 與 cleanup failure 分離
* teardown results 寫入 report.json

### Failure Example

```text
setup: PASSED
scenario: FAILED
teardown: PASSED
global_teardown: PASSED
final status: FAILED
```

另一種情況：

```text
scenario: FAILED
teardown: FAILED
final status: FAILED

primary_error:
  scenario command failed

cleanup_errors:
  teardown command failed
```

### Learning Focus

* try／finally
* failure preservation
* cleanup guarantees
* hooks
* multi-error reporting

### Status

Planned

---

## v1.9 — Execution Summary

### Goal

提供可讀、可查詢的完整 execution summary。

### Core Features

* RunSummary
* stage duration summary
* total duration
* passed step count
* failed step count
* skipped step count
* retry count
* timeout count
* validation summary
* recorder summary
* first failure
* failure category aggregation
* console summary
* JSON summary
* exit code strategy

### Example Summary

```text
Test Case: power_idle_test
Device: ABC123
Status: FAILED
Duration: 125.3 seconds

Stages:
- global_setup: PASSED
- setup: PASSED
- scenario: FAILED
- teardown: PASSED
- global_teardown: PASSED

Steps:
- Passed: 6
- Failed: 1
- Skipped: 0
- Retried: 2

First Failure:
- Stage: scenario
- Step: run_idle_scenario
- Exit Code: 1
```

### Learning Focus

* Aggregation
* reporting model
* observability
* diagnostics
* exit code design

### Status

Planned

---

## v1.10 — Job Model

### Status

Planned

---

## v1.11 — Batch Runner

### Status

Planned

---

## v1.12 — Multi-Process Execution

### Status

Planned

---

## v1.13 — Concurrency Limit

### Status

Planned

---

## v1.14 — Resource / Device Lock

### Status

Planned

---

## v2.0 — Controller and Worker

### Goal

將單機 Device Test Runner 擴展為可進行 remote execution 的分散式測試系統。

### High-Level Architecture

```text
User / CLI / Web UI
        ↓
Controller
        ↓
Scheduler / Dispatcher
        ↓
Worker
        ↓
Device + Recorder + Test Scripts
```

### Controller Responsibilities

* 接收 execution request
* 驗證 request
* 選擇 worker
* dispatch test run
* 追蹤 worker state
* 追蹤 run state
* 收集 execution result
* 處理 worker disconnect
* 提供 execution history

### Worker Responsibilities

* 回報 worker capability
* 回報 device inventory
* 接收 execution request
* 執行 local Device Test Runner
* 上傳 artifacts
* 回報 progress
* 回報 final result
* 處理 cancellation

### Core Features

* Controller
* Worker
* ExecutionRequest
* WorkerState
* RunState
* job queue
* dispatch mechanism
* worker registration
* heartbeat
* remote execution
* artifact upload
* result synchronization
* basic scheduling policy
* retry on worker failure

### Possible Implementation Stages

#### v2.0.0

* Single controller
* Single worker
* HTTP-based dispatch
* synchronous execution

#### v2.1.0

* Multiple workers
* worker capability registration
* basic worker selection

#### v2.2.0

* job queue
* asynchronous execution
* run status polling

#### v2.3.0

* heartbeat
* worker offline detection
* worker recovery

#### v2.4.0

* artifact upload
* centralized report storage
* execution history

### Learning Focus

* Distributed systems
* controller／worker architecture
* dispatch
* remote execution
* state machines
* failure recovery
* resource scheduling

### Status

Future

---

# 4. Keyword-Driven Direction

Keyword-Driven 是 Device Test Runner 的另一條重要發展方向。

它不一定要等到 v2.0 才開始，但應建立在穩定的 lifecycle、executor 與 artifact foundation 上。

## Goal

讓不熟悉 Python 或 Bash 的 Lab 成員，可以使用高階 domain keywords 組合測試流程。

### Example

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

## Planned Components

* KeywordRegistry
* KeywordExecutor
* KeywordDefinition
* KeywordContext
* KeywordResult
* Domain Keyword Library
* parameter validation
* keyword discovery
* keyword documentation
* keyword aliases
* reusable keyword composition

## Example Domain Libraries

```text
keywords/
├── android/
│   ├── adb_keywords.py
│   ├── app_keywords.py
│   └── system_keywords.py
├── power/
│   ├── recorder_keywords.py
│   └── measurement_keywords.py
├── device/
│   ├── flash_keywords.py
│   └── reboot_keywords.py
└── validation/
    └── artifact_keywords.py
```

## Design Principle

YAML 仍然是底層 scenario definition。

Keyword-Driven layer 應建立在 executor 與 lifecycle 之上，而不是取代原有 command execution。

```text
YAML
  ↓
Keyword Definition
  ↓
Keyword Registry
  ↓
Keyword Executor
  ↓
Command / Python Function / Remote Action
```

---

# 5. Future Extensions

以下方向暫時不屬於近期核心版本，但可作為後續擴展。

## 5.1 CLI

* run scenario
* validate config
* list keywords
* list devices
* inspect report
* rerun failed test
* show execution summary

Example:

```bash
device-test-runner run configs/power_idle.yaml
device-test-runner validate configs/power_idle.yaml
device-test-runner keywords list
device-test-runner report show artifacts/run-001/report.json
```

## 5.2 Web UI

* 建立 execution request
* 選擇 device
* 選擇 scenario
* 查看即時 log
* 查看 run status
* 下載 artifacts
* 查看 execution history
* 查看 worker state

Web UI 不應直接執行 domain logic，而應呼叫 Controller API。

## 5.3 Device Inventory

* device serial
* product
* build
* Android version
* connection state
* assigned worker
* current reservation
* capability labels

## 5.4 Scheduling

* FIFO
* device capability matching
* worker load balancing
* device reservation
* test priority
* retry scheduling
* maximum concurrent runs

## 5.5 Observability

* structured logging
* execution metrics
* worker metrics
* device availability metrics
* failure rate
* average test duration
* retry rate
* timeout rate
* artifact validation failure rate

## 5.6 Persistence

* execution history database
* worker registry
* device inventory
* artifact metadata
* test result history
* trend analysis

---

# 6. Version Management Strategy

Device Test Runner 使用 Semantic Versioning：

```text
MAJOR.MINOR.PATCH
```

Example:

```text
v1.4.0
v1.4.1
v1.5.0
v2.0.0
```

## MAJOR

重大架構改變或不相容變更。

Example:

```text
v1.x single-machine runner
v2.0 controller／worker architecture
```

## MINOR

新增向下相容的功能。

Example:

```text
v1.4 artifact validation
v1.5 retry policy
```

## PATCH

修正 bug 或小型改善。

Example:

```text
v1.4.1 fix file size validation
v1.4.2 fix report serialization
```

---

# 7. GitHub Project Mapping

每個 Roadmap version 對應一個 GitHub Milestone。

```text
Roadmap Version
    ↓
GitHub Milestone
    ↓
GitHub Issues
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

## Example Milestone

```text
v1.4 Artifact Validation
```

Related Issues:

```text
- Define ValidationResult model
- Define ValidationRule abstraction
- Implement FileExistsRule
- Implement MinimumFileSizeRule
- Implement ArtifactValidator
- Aggregate validation status
- Add unit tests
- Add integration tests
- Update architecture documentation
```

## Suggested Project Status

```text
Backlog
Todo
In Progress
Review
Done
```

---

# 8. Definition of Done

每一個版本完成前，至少需要滿足：

* 功能已實作
* unit tests 通過
* integration tests 通過
* example YAML 可執行
* result.json 格式已確認
* error handling 已覆蓋
* README 或 docs 已更新
* CHANGELOG.md 已更新
* GitHub Issues 已關閉
* Milestone 已完成
* Git tag 已建立
* GitHub Release notes 已建立

---

# 9. Current Priorities

目前已完成 v1.5.0，接下來的開發優先順序：

```text
1. v1.6 Timeout and Cancellation
2. v1.7 Recorder Lifecycle
3. v1.8 Hook and Teardown Guarantees
4. v1.9 Execution Summary
5. v1.10～v1.14 Job、batch、multi-process、concurrency 與 device lock
6. 單機 execution model 穩定後進入 v2.0 Controller／Worker
```

近期不優先處理：

* 複雜 Web UI
* 多租戶權限
* Kubernetes
* 大型 message queue
* 過度抽象的 plugin system
* 過早的 microservices 拆分
* 完整 distributed scheduling

目前最重要的是先建立可靠的單機 execution lifecycle。

---

# 10. Long-Term Outcome

Device Test Runner 的長期目標，是從單機的測試流程執行器，逐步演化為 Device Validation Platform 的核心執行層。

```text
Scripts
   ↓
Runner
   ↓
Lifecycle
   ↓
Artifacts
   ↓
Validation
   ↓
Recorder Coordination
   ↓
Remote Worker
   ↓
Controller
   ↓
Device Test Platform
```

這個專案同時也是以下能力的實作練習：

* Python software design
* Test architecture
* Test lifecycle
* Orchestration
* Process management
* Artifact management
* Error handling
* Reliability
* Distributed systems
* Developer productivity
* Test infrastructure
* Platform engineering
