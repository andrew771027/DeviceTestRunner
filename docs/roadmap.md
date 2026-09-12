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

## v1.5.1 — Artifact-Aware Retry

### Goal

讓 artifact validation 成為 step attempt 成功條件的一部分，使 command 成功但輸出 artifact 尚未就緒或內容無效時，仍可依 retry policy 重試該步驟。

### Core Features

* `after_step` 將 artifact validation rule 綁定到指定 step
* `retry_on_failure` 明確控制 artifact failure 是否觸發 retry
* 每次 attempt 在 command 成功後立即執行該 step 的 retry-enabled rules
* command 與綁定的 artifact rules 全部通過，attempt 才算成功
* 每次 attempt 的 validation results 寫入 `StepAttemptResult` 與 `result.json`
* 非 retry-enabled rules 保留在 lifecycle 結束後的 final validation
* artifact retry exhausted 時停止後續 scenario steps，並維持 teardown guarantees

### Example Configuration

```yaml
retry:
  max_attempts: 3
  delay_seconds: 1

artifact:
  output_dir: artifacts
  validation:
    rules:
      - name: validate_power_csv
        type: csv_content
        path: results/power.csv
        after_step: run_power_test
        retry_on_failure: true
        required_columns:
          - timestamp
          - power
        min_rows: 2
```

### Status

Completed

---

## v1.5.2 — Failure Classification

### Goal

將 process 與 artifact failure 轉換為一致、可報告且可供 retry policy 使用的 failure type，提升 device test failure triage 的速度與可追蹤性。

### Core Features

* `FailureClassifier`
* `NONE`、`TIMEOUT`、`DEVICE_OFFLINE`、`PROCESS_ERROR`、`ARTIFACT_MISSING`、`ARTIFACT_INVALID`
* timeout 與常見 device-offline 訊息分類
* process failure 與 artifact failure priority
* failure-type-aware retry decision
* per-attempt failure type 寫入 `StepAttemptResult` 與 `result.json`
* real subprocess integration coverage

### Status

Completed

---

## v1.5.3 — Selective Retry and Artifact Criticality

### Goal

讓使用者依 failure type 精確控制 retry，並區分會阻擋測試結果的 required artifact 與僅供診斷的 optional artifact。

### Core Features

* `retry.retry_on` 接受 `timeout`、`device_offline`、`process_error`、`artifact_missing`、`artifact_invalid`
* 未設定 `retry_on` 時不重試；重複值去重，未知值與 `none` 拒絕載入
* artifact rule 的 `required` 預設為 `true`
* optional artifact validation failure 保留於 report，但不影響 attempt 或 run status
* retry cleanup 僅移除 run directory 內的 required targets
* summary 新增 `failed_required_artifact_rules`

### Status

Completed

---

## v1.6.0 — Cancellation Foundation

### Goal

在既有 timeout 與 selective retry 上，提供由 Python 呼叫端控制的取消流程及可追蹤結果。

### Implemented Features

* `CancellationToken`（threading.Event）、可重複 cancel 與 exception helper。
* Runner 在一般 stage／attempt 邊界檢查取消；executor polling 區分 cancellation 與 timeout。
* 直接子程序 terminate，等待兩秒後必要時 kill；保留已讀取輸出。
* 取消不重試；retry delay 以最多 0.1 秒 polling 回應取消。
* Reachable cleanup 使用新的 execution token，所有 artifact rules 仍執行 final validation。
* `cancel_requested`、attempt `timed_out`／`cancelled`、step `cancelled`、`cancelled_steps` 與 `CANCELLED` status。
* 本機完整 suite：153 passed in 39.39s（2026-09-12，Python 3.14）；150 個函式均有 reviewed Given／When／Then。

### Remaining Work

* v1.6.1：process-group／child cleanup、輸出收尾、retry process cleanup 與 SIGINT。
* v1.6.2：run-level deadline 與 timeout cancellation request。
* v1.6.3：cleanup scope／timeout、取消邊界路由與 partial artifact／report policy。
* `configs/sample.yaml` 全數通過的示範流程。
* Tag、GitHub Release、issue closure 與手動文件 CI 成功執行的驗證。

### Status

Foundation implemented and locally tested; release pending. 不將完整 Timeout and Cancellation guarantees 標記為完成。

詳細證據：[Architecture](architecture/architecture_v1.6.0.md)、[Test Matrix](test_matrix/test_matrix_v1.6.0.md)、[Definition of Done](definition_of_done/definition_of_done_v1.6.0.md)。

---

## v1.6.1 — Safe Process Termination

### Goal

補齊 Process Lifecycle／Cleanup，確保取消、timeout 與 retry 不留下仍在執行的程序或無法結束的輸出 reader。

### Core Features

* terminate → grace period → kill，提供 graceful cancellation。
* Process group termination 與 child process cleanup。
* stdout／stderr threads 正常收尾，保留已讀取輸出，避免後代程序持有 pipe 造成無限等待。
* Retry 前確認前一次 attempt 的程序與輸出 reader 已完成清理，才啟動下一次 attempt。
* Ctrl+C／SIGINT 轉為 cancellation request，沿用 runner 取消流程。
* 可選：第二次 Ctrl+C force exit；需明確說明強制離開可能中斷 cleanup 與 report 寫入。

### Relationship to v1.6.0

v1.6.0 已有直接 `Popen` 程序的 terminate → 固定兩秒等待 → kill，以及正常路徑的 stdout／stderr thread join。本版本擴充到 process group、後代程序與各種結束路徑的收尾保證，不重做 cancellation token。

目前使用 `shell=True`，沒有建立獨立 process group；reader join 沒有等待上限。Runner 雖然等待 executor 返回才 retry，但不代表前一次的後代程序已清乾淨；既有 retry cleanup 主要處理 required artifact targets。`main.py` 尚未接上 SIGINT。

### Acceptance Focus

* 取消、step timeout 與 retry 後沒有殘留的受管理子程序。
* 拒絕 graceful termination 的程序會在 grace period 後被強制終止。
* stdout／stderr 收尾可完成，下一次 attempt 不與前一次程序重疊。
* 明確定義支援平台的 process-group 與 signal 行為；SIGTERM 接線另行決定範圍。

### Status

Planned

---

## v1.6.2 — Run-level Timeout

### Goal

在既有 per-step timeout 之外，限制一般 run 工作的總執行時間，並透過統一 cancellation 流程停止工作。

### Core Features

* 新增 `run_timeout_seconds` 設定與驗證，未設定時維持既有行為。
* Run timeout 轉為 cancellation request，停止一般 stages、執行中的 command 與 retry delay。
* 明確區分 step timeout 與 run timeout，報告保留取消原因。
* Step timeout 可依 `retry_on` 重試；run timeout 不應因下一次 attempt 而重設 deadline 或繼續一般工作。

### Relationship to v1.6.0

v1.6.0 只有 `timeout_second` 的 step deadline，沒有 run deadline。現有 token 只有取消狀態，`cancel_requested` 也不記錄原因，因此需要擴充原因資訊，避免將 run timeout 和使用者取消混為一談。

相容性方向：沿用 cancellation 執行路徑；保留既有 attempt `timed_out` 對 step timeout 的意義。Run-level 原因欄位與最終 status 的 schema 在實作時明確定義，不能僅將 run timeout 冒充為某一步的 TIMEOUT。

### Acceptance Focus

* 多個未超時的 steps 累計仍可觸發 run timeout。
* Retry delay 與 attempts 共用同一個 run deadline。
* Run deadline 停止一般工作後仍進入 cleanup；cleanup 使用 v1.6.3 的獨立 scope／timeout。
* 明確定義計時起點、涵蓋階段與 report finalization 邊界；run timeout 不等同整個程序必須立即退出。

### Status

Planned

---

## v1.6.3 — Cancellation-aware Cleanup

### Goal

將 cancellation 後的 cleanup 從現有 best effort 路由提升為明確的 scope、時間限制與 partial artifact／report policy。

### Core Features

* Cancellation 後執行符合 lifecycle 條件的 teardown 與 global_teardown。
* Teardown 獨立 cancellation scope，不直接沿用已取消的一般工作 token。
* Teardown timeout，明確定義每個 step 與整體 cleanup 的時間預算。
* Partial artifact／report policy：保留已完成 attempt 與輸出，說明未完成或未產生 artifact 的判定與報告方式。
* 保留主要取消原因及 cleanup failure／timeout，避免清理結果覆蓋原始原因。

### Relationship to v1.6.0

v1.6.0 已在進入 setup 後的取消路徑執行 teardown，並對每個 cleanup attempt 建立新 token；cleanup command 也已有一般 step timeout。這些是本版本的基礎，不是全新功能。

尚未具備 cleanup scope 的整體 deadline 與管理方式。Retry delay 仍讀取原始已取消 token，可能略過 cleanup delay；global_setup 成功後、進入 setup 前的取消也可能跳過 teardown。需要明確定義這些邊界，並處理未預期例外時的 finalization。

目前 run 結束後仍驗證所有 artifact rules，missing required artifacts 可與 CANCELLED 並存。新的 partial policy 應保留診斷證據，明確決定哪些規則執行或標記未完成，不默默將缺失 artifact 改為通過。

### Acceptance Focus

* 覆蓋 run 開始前、global_setup 中、global_setup 完成邊界、setup／scenario 中及 retry delay 的取消路由。
* 不將「取消後 teardown」解讀為所有情況無條件執行：尚未取得資源的階段應依 lifecycle contract 決定清理責任。
* 一般 run 已取消或逾時時，cleanup 仍可執行，但受自己的 timeout 限制。
* Cleanup 失敗、超時或 partial artifact 不會遺失原始取消原因；正常受控收尾可寫出 report。

### Status

Planned

---

### v1.6.x Scope Alignment

| 項目 | v1.6.0 現況 | 後續版本責任 |
| --- | --- | --- |
| terminate → wait → kill | 已有直接程序、固定兩秒等待 | v1.6.1 補齊程序群組、後代程序及完整收尾 |
| stdout／stderr join | 正常路徑已有，未保證有界完成 | v1.6.1 處理 pipe、reader 及異常路徑 |
| retry cleanup | 已清理 required artifacts；未保證後代程序結束 | v1.6.1 增加 process cleanup 保證 |
| Ctrl+C／SIGINT | CLI 未接線 | v1.6.1 接入 token cancellation |
| run timeout | 尚未實作 | v1.6.2 新增 deadline 與取消原因 |
| 取消後 teardown | 已有部分路由與每次 attempt 的新 token | v1.6.3 定義完整路由與 cleanup scope |
| teardown timeout | 已套用一般 step timeout | v1.6.3 定義 cleanup 整體時間預算 |
| partial report | 已保留 attempt 輸出並做 final validation | v1.6.3 明確制定 partial policy 與 finalization |

三個版本可依序建立在 v1.6.0 上，沒有必然衝突；重疊項目應視為既有基礎的強化。需特別對齊 run deadline 與 cleanup deadline，以及 step timeout 與 run cancellation 的報告語意。

---

## v1.7.x — YAML Variables, Environment and Runtime Context

### Goal

讓 YAML 可重用靜態參數、設定 command environment，並引用 runner 產生的執行資訊，減少 scripts 與 configuration 中重複的路徑及參數。

安排在 v1.6.3 之後、v1.8 Recorder Lifecycle 之前：先穩定 attempt 與 cleanup 的生命週期，再定義 context 的有效範圍；後續 recorder、hooks 與 job model 可共用這套設定能力。

### Core Features

| 能力 | 責任 | 解析時機 |
| --- | --- | --- |
| Static Variable Substitution | YAML `variables` 定義固定值並在支援的設定欄位引用 | 載入 configuration 時 |
| Environment | 引用 host environment，並透過 run／step `environment` 設定傳入 subprocess 的環境 | 每次 run 建立 host environment snapshot；每個 attempt 組合 subprocess environment |
| Runtime Context | 提供 runner 管理的 run、stage、step、attempt 資訊 | 對應 run／stage／attempt 建立後，在使用欄位前解析 |

* 使用獨立 namespaces，例如 `vars`、`env`、`context`，避免同名變數來源不明。
* 定義可替換欄位、缺少變數的錯誤、literal escaping、巢狀引用與循環引用檢查。
* Environment 合併順序：host snapshot → run environment → step environment；runner 保留欄位不可被覆寫。
* Runtime context 為唯讀；初期範圍包含 run ID、run artifact directory、stage、step name、attempt number。
* 不使用任意 Python expression、eval 或 command substitution 作為模板功能。

### v1.7.0 — Static Variables

#### Goal

載入 YAML 時替換固定參數，建立後續 Environment 與 Runtime Context 共用的解析規則。

#### Scope and Acceptance

* 支援 `variables` 與 `vars` namespace，定義可引用的設定欄位。
* 支援重複引用、literal escaping 與明確的缺值錯誤；偵測巢狀引用中的循環。
* 區分完整 scalar 引用與字串內插，替換後仍執行欄位型別驗證。
* 不含變數語法的既有 YAML 維持相容；不執行任意 expression 或 shell command。

#### Status

Planned

### v1.7.1 — Environment

#### Goal

在靜態變數基礎上提供 host、run、step environment 設定與一致的覆寫順序。

#### Scope and Acceptance

* 每次 run 建立 host environment snapshot，以 `env` namespace 引用。
* 合併順序為 host snapshot → run environment → step environment；不修改 host `os.environ`。
* 可使用 v1.7.0 靜態變數設定 environment 值，缺少 host 變數時提供錯誤或顯式預設值。
* 保留 `DEVICE_TEST_RUNNER_ROOT`、`RUN_ARTIFACT_DIR`，禁止使用者覆寫 runner 保留欄位。
* 不將完整環境或敏感值寫入 report／模板診斷，明確定義 shell quoting 責任。

#### Status

Planned

### v1.7.2 — Runtime Context

#### Goal

在 run 與 attempt 建立後，提供唯讀的執行資訊，供設定與 subprocess environment 使用。

#### Scope and Acceptance

* `context` namespace 提供 run ID、artifact directory、stage、step 與 attempt。
* 沿用 runner 的既有識別值；retry 更新 attempt，cleanup 更新 stage／step，run 資訊保持一致。
* v1.7.1 的 environment mapping 可引用當次有效 context。
* 定義欄位解析時機；禁止尚未建立或已失效的 context 引用，避免 run directory 自我依賴。
* Final validation 的 run scope 與 attempt scope 分開，不隱含採用最後一次 attempt。

#### Status

Planned

### Proposed YAML

以下為 v1.7.0～v1.7.2 完成後的整合規劃語法，尚未實作；實作前需確認欄位名稱與替換範圍。

```yaml
variables:
  serial: emulator-5566
  test_mode: idle

environment:
  DEVICE_SERIAL: "${{ vars.serial }}"
  LAB_PROFILE: "${{ env.LAB_PROFILE }}"

lifecycle:
  scenario:
    steps:
      - name: measure
        type: command
        command: bash "$DEVICE_TEST_RUNNER_ROOT/scripts/measure.sh"
        timeout_second: 30
        environment:
          TEST_MODE: "${{ vars.test_mode }}"
          ATTEMPT_NUMBER: "${{ context.attempt }}"
          OUTPUT_DIR: "${{ context.run_artifact_dir }}"
```

此片段展示新增設定，其他必要 sections 仍需提供；`measure.sh` 為示意 script。`${{ ... }}` 是提議的 runner template 語法；既有 `$NAME`／`${NAME}` 仍由 shell 展開。

### Relationship to v1.6.0

目前 ConfigLoader 直接建立 models，沒有通用 YAML variable substitution、run／step environment mapping 或 runtime context resolver。Executor 已繼承 `os.environ`，並注入 `DEVICE_TEST_RUNNER_ROOT` 與 `RUN_ARTIFACT_DIR`；這是既有 environment 基礎，應保留相容性。

新增 context 需沿用已建立的 run directory、stage 與 attempt 資訊，而不是再建立一套不一致的識別值。Retry 每次重新產生 attempt context；cleanup 使用自己的 stage／step context，並保留同一次 run 的資訊。

### Acceptance Focus

* 同一靜態變數可用於多個支援欄位；未知引用與循環引用提供欄位位置明確的錯誤。
* 規定替換後的型別驗證：完整 scalar 引用與字串內插分開處理，不能讓字串替換繞過 timeout 等欄位的驗證。
* Host environment 缺值有明確錯誤或顯式預設值；不修改 host 的 `os.environ`。
* Run／step environment 覆寫順序可測試，保留的 runner environment 與 context 不可被使用者冒用。
* Attempt number 隨 retry 更新，run ID 與 run directory 在同次執行中維持一致。
* 尚未建立 run directory 時，不允許用它反過來決定自身位置；final validation 不可引用已失效或含糊的 attempt context。
* Environment 值傳入 subprocess 時保留原值；對 command 字串內插明確定義 quoting 責任，避免把資料誤當 shell 語法。
* Report 不直接序列化整份 host environment，敏感值不因模板診斷而被列印。
* 不含新語法的既有 YAML 與 `$RUN_ARTIFACT_DIR` scripts 維持既有行為。

### Scope Boundaries

初期不包含跨 step output 引用、secret manager、條件式、迴圈或完整 template language。這些功能需要額外定義資料依賴與失敗語意，可在 job／keyword-driven 階段另行規劃。

### Status

Planned

---

## v1.8 — Recorder Lifecycle

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

## v1.9 — Hook and Teardown Guarantees

v1.6.3 負責 cancellation-aware cleanup 的基礎 scope、timeout 與 partial policy；本版本在其上擴充可重用 hooks、recorder 整合與多重錯誤呈現，避免重複實作相同的取消清理機制。

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

## v1.10 — Execution Summary

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

## v1.11 — Job Model

### Status

Planned

---

## v1.12 — Batch Runner

### Status

Planned

---

## v1.13 — Multi-Process Execution

### Status

Planned

---

## v1.14 — Concurrency Limit

### Status

Planned

---

## v1.15 — Resource / Device Lock

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
v1.5.1
v1.5.2
v1.5.3
v1.6.0
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
v1.5.1 artifact-aware retry
v1.5.2 failure classification
v1.5.3 selective retry and artifact criticality
```

## PATCH

修正 bug 或小型改善。

Example:

```text
v1.4.1 fix file size validation
v1.4.2 fix report serialization
v1.5.2 add failure classification and diagnostics
v1.5.3 add selective retry and optional artifacts
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

目前已實作並本機驗證 v1.6.0 cancellation foundation；完整取消保證與發佈仍待完成。接下來的開發優先順序：

```text
1. v1.6.1 Safe Process Termination
2. v1.6.2 Run-level Timeout
3. v1.6.3 Cancellation-aware Cleanup
4. v1.7.x YAML Variables, Environment and Runtime Context
5. v1.8 Recorder Lifecycle
6. v1.9 Hook and Teardown Guarantees
7. v1.10 Execution Summary
8. v1.11～v1.15 Job、batch、multi-process、concurrency 與 device lock
9. 單機 execution model 穩定後進入 v2.0 Controller／Worker
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
