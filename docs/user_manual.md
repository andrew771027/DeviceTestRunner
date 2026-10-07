# Device Test Runner 使用手冊

適用版本：v1.6.3。本手冊說明如何設定、執行與判讀測試。安裝步驟見 [README](../README.md#安裝)。

先完成第一個流程，再依需要查閱設定參考。本文的「必填／選填」以 YAML 經 ConfigLoader 載入的行為為準；Python API 的差異另行說明。

- [建立並執行第一個流程](#建立並執行第一個流程)
- [設定欄位參考](#設定欄位參考)
- [Artifact 驗證參考](#artifact-驗證參考)
- [路徑與環境變數](#路徑與環境變數)
- [CLI 與結果判讀](#cli-與結果判讀)
- [透過 Python API 取消](#透過-python-api-取消)


## 建立並執行第一個流程

將以下內容存為 `configs/hello.yaml`。此範例不需要連接裝置，會產生一份 CSV 並檢查內容。五個 lifecycle 階段都需提供 `steps`；不使用的階段填入 `[]`。

```yaml
test_case:
  id: hello
  name: Hello Runner
  description: Create and validate a CSV file.
device:
  serial: demo
  product: demo
  build: demo
lifecycle:
  global_setup:
    steps: []
  setup:
    steps: []
  scenario:
    steps:
      - name: write_csv
        type: command
        command: 'printf "timestamp,power\n1,110\n" > result.csv'
        timeout_second: 10
  teardown:
    steps: []
  global_teardown:
    steps: []
artifact:
  output_dir: artifacts
  validation:
    rules:
      - name: check_csv
        type: csv_content
        path: result.csv
        required_columns: [timestamp, power]
        min_rows: 1
```

在專案根目錄執行：

```bash
poetry run python main.py --config configs/hello.yaml
```

CLI 會顯示最終狀態。到 `artifacts/` 下該次執行目錄查看 `result.json`、`result.csv` 與步驟的 stdout／stderr log。以報告的 `summary.status` 判斷結果：`PASSED`、`FAILED`、`CANCELLED` 或 `TIMED_OUT`。

接著可將 `command` 替換成自己的腳本或裝置命令。命令的工作目錄是該次 run directory；引用專案內腳本時使用 `$DEVICE_TEST_RUNNER_ROOT`，取得輸出目錄則使用 `$RUN_ARTIFACT_DIR`。例如：

```yaml
command: bash "$DEVICE_TEST_RUNNER_ROOT/scripts/run_scenario.sh"
```

使用 ADB 等外部命令前，需自行安裝工具並確認裝置連線。`device` 欄位用於報告資料，裝置選擇仍需在命令中指定。

專案另提供 [sample.yaml](../configs/sample.yaml)，展示多個階段、重試與驗證規則：

```bash
poetry run python main.py --config configs/sample.yaml
```

此設定包含失敗命令與缺少產物的情境，適合觀察失敗處理，不應以全部通過作為安裝成功的條件。

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

上述為一般失敗路由。global_setup 成功後即具備 teardown 條件，即使隨後取消而尚未進入 setup，也會執行 teardown。run 開始前已取消或 global_setup 未成功時，只嘗試 global_teardown。兩個 cleanup stages 共用獨立 token；cleanup deadline 到期後不啟動剩餘 steps。受控收尾不涵蓋未處理 Python exception 或 KeyboardInterrupt。

最終狀態先依 run 取消原因判定：RUN_TIMEOUT 為 `TIMED_OUT`，USER_REQUEST 為 `CANCELLED`。沒有上述原因時，先檢查 cleanup failure（FAILED），再檢查 cancelled steps（CANCELLED）、failed／skipped steps 與 required artifact failure（FAILED）；其餘為 PASSED。

## 設定測試流程

以下設定示範裝置命令、整次執行逾時、重試與 CSV 驗證。可另存為 YAML 後透過 `--config` 指定；請先將裝置序號 `ABC123` 換成自己的序號：

```yaml
test_case:
  id: power_idle_test
  name: Power Idle Test
  description: Measure device power consumption during idle state.

device:
  serial: ABC123
  product: pixel
  build: build_12345

run_timeout_seconds: 3600

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

`after_step` 將 validation rule 綁定到指定 step，runner 會在該 step 每次 command 成功後立即驗證。`required` 預設為 `true`：required rule 失敗會使 attempt 失敗，且只有 failure type 出現在 `retry.retry_on`、尚未達 `max_attempts` 時才重試；`required: false` 的失敗仍寫入 report，但不影響 step 或 run 狀態。Lifecycle 結束後會再次對所有規則執行 final validation，包括有 `after_step` 的規則。YAML 未設定 `retry_on` 時預設為空清單，因此不重試；`none`、`cancelled` 與未知值會被拒絕。直接使用 Python `RetryConfig()` 的預設清單不同，使用 Python API 時請明確指定重試條件。

## 設定欄位參考

YAML 根節點必須是 mapping（鍵值表）。欄位名稱區分大小寫；`timeout_second` 是單數，scope timeout 則使用 `*_seconds`。以下型別表示預期用法；loader 不會完整驗證每個欄位的型別或未知欄位，請勿將「可載入」視為設定一定有效。

### 頂層設定

| 變數名稱 | 必填／選填 | 型別與預設值 | 意義與用途 | 範例 |
| --- | --- | --- | --- | --- |
| `test_case` | 必填 | mapping；無預設 | 識別本次測試，寫入報告 | 見下表 |
| `device` | 必填 | mapping；無預設 | 裝置描述，寫入報告；不會自動連線或選擇裝置 | 見下表 |
| `lifecycle` | 必填 | mapping；無可用 YAML 預設 | 安排五個階段與命令 | `scenario: {steps: []}`，其他階段也需提供 |
| `artifact` | 必填 | mapping；無預設 | 指定輸出目錄與驗證規則 | `output_dir: artifacts` |
| `retry` | 選填 | mapping；最多一次、不延遲、不重試 | 指定可重試失敗與上限 | `max_attempts: 3` |
| `run_timeout_seconds` | 選填 | 有限正數；省略／null 為不限時 | 限制 normal scope，含準備、scenario 與 retry delay | `3600` |
| `cleanup_timeout_seconds` | 選填 | 有限正數；省略／null 為不限時 | teardown 與 global_teardown 共用清理預算 | `60` |

兩個 scope timeout 拒絕字串、bool、零、負數、NaN 與 Infinity。即使不使用某個 lifecycle 階段，也需要填入 `steps: []`。省略階段會因 loader 讀取 `steps` 而失敗。

### 測試與裝置資訊

| 變數名稱 | 必填／選填 | 型別與預設值 | 意義與用途 | 範例 |
| --- | --- | --- | --- | --- |
| `test_case.id` | 必填 | 字串；無預設 | 測試識別碼，也用於 run directory 名稱 | `power_idle` |
| `test_case.name` | 必填 | 字串；無預設 | 報告中供人閱讀的名稱 | `Power Idle Test` |
| `test_case.description` | 必填 | 字串；無預設 | 說明測試目的 | `Measure idle power.` |
| `device.serial` | 必填 | 字串；無預設 | 報告中的裝置序號 | `ABC123` |
| `device.product` | 必填 | 字串；無預設 | 報告中的產品名稱 | `pixel` |
| `device.build` | 必填 | 字串；無預設 | 報告中的版本描述 | `build_001` |

`device.serial` 不會自動帶入命令。使用 ADB 時自行寫入 `adb -s ABC123 ...`；目前沒有 YAML 變數替換功能。

### 階段與步驟

`lifecycle.global_setup`、`setup`、`scenario`、`teardown`、`global_teardown` 都必填，各自包含 `steps` 清單。用途與失敗路由見 [測試生命週期](#測試生命週期)。

下表中的 `steps[]` 代表任何階段的一個步驟，例如 `lifecycle.scenario.steps[0]`。

| 變數名稱 | 必填／選填 | 型別與預設值 | 意義與用途 | 範例 |
| --- | --- | --- | --- | --- |
| `lifecycle.<stage>.steps` | 必填 | list；無 YAML 預設 | 按清單順序執行；空清單跳過該階段工作 | `[]` |
| `steps[].name` | 必填 | 字串；無預設 | 步驟名稱、log 目錄名稱與 after_step 比對值 | `write_csv` |
| `steps[].type` | 必填 | 字串；無預設 | 描述步驟類型；目前 executor 一律執行 command | `command` |
| `steps[].command` | 必填 | shell 命令字串；無預設 | 在 run directory 執行的命令 | `echo hello` |
| `steps[].timeout_second` | 選填 | 秒數；YAML 預設 `60` | 限制每次 attempt 的程序執行時間；重試各有自己的 step timeout | `30` |

請為 steps 使用不重複、適合作為目錄名稱的 `name`。目前未強制檢查唯一性；重複名稱可能共用 log 路徑，且 after_step 會比對所有同名步驟。`type` 不會切換至 Python、keyword 或其他 executor。Bash 語法請明確使用 `bash -c '...'`，不要假設預設 shell 是 Bash。

### 重試設定

| 變數名稱 | 必填／選填 | 型別與預設值 | 意義與用途 | 範例 |
| --- | --- | --- | --- | --- |
| `retry.max_attempts` | 選填 | 整數；`1` | 總執行次數，包含第一次；必須至少 1 | `3` 表示最多重試兩次 |
| `retry.delay_seconds` | 選填 | 非負秒數；`0.0` | 可重試失敗後，下一次 attempt 前的等待時間 | `1` |
| `retry.retry_on` | 選填 | 字串 list；YAML 預設 `[]` | 只重試列出的 failure type；重複值會去重 | `[timeout, device_offline]` |

可用值是 `timeout`、`device_offline`、`process_error`、`artifact_missing`、`artifact_invalid`。`none`、`cancelled` 與未知值會被拒絕。max_attempts 大於 1 仍需設定 retry_on 才會重試。取消永不重試；cleanup 的 retry delay 也受 cleanup token 控制。

```yaml
retry:
  max_attempts: 3
  delay_seconds: 1
  retry_on: [timeout, artifact_missing, artifact_invalid]
```

### Python API 的預設差異

直接建立 `RunnerConfig` 時，test_case、device、lifecycle、retry、artifact 都是必要建構參數。`LifecycleConfig()` 可省略階段，dataclass 預設空 steps；YAML loader 則需要五個階段的 steps。`LifecycleStepContent` 建構時必須提供 timeout_second，沒有 YAML 的 60 秒預設。

`RetryConfig()` 的 retry_on 預設包含上述五種失敗，YAML 省略 retry_on 則為空清單。使用 Python API 時明確傳入 `retry_on=[]` 或需要的 failure types。Dataclass 不執行 YAML loader 的 timeout 驗證。

## Artifact 驗證參考

### 輸出與共用規則

| 變數名稱 | 必填／選填 | 型別與預設值 | 意義與用途 | 範例 |
| --- | --- | --- | --- | --- |
| `artifact.output_dir` | 必填 | 路徑字串；無預設 | 每次 run directory 的父目錄 | `artifacts` |
| `artifact.validation` | 選填 | mapping；空規則 | 設定輸出檔案檢查 | `rules: []` |
| `artifact.validation.rules` | 選填 | list；`[]` | 逐條記錄驗證結果 | 見下列範例 |
| `rules[].name` | 必填 | 字串；無預設 | 報告中辨識驗證結果 | `power_csv` |
| `rules[].type` | 必填 | 字串；無預設 | 選擇驗證方式 | `csv_content` |
| `rules[].path` | 必填 | 路徑字串；無預設 | 要檢查的檔案或目錄；相對 run directory 解析 | `results/power.csv` |
| `rules[].after_step` | 選填 | step name；`null` | 指定 command 成功後的 attempt-level 驗證；按名稱精確比對 | `measure_power` |
| `rules[].required` | 選填 | bool；`true` | 失敗是否影響 attempt 與 final status | `false` 用於診斷資料 |

所有規則都會做 final validation，包括設定 after_step 的規則。沒有 after_step 的規則只做 final validation。after_step 不存在時不會觸發 attempt-level 驗證；目前不拒絕這種設定。只有 command 成功後才執行 attempt-level 驗證，取消的 attempt 會跳過。

required 規則失敗可觸發符合 retry_on 的重試。重試前會清理綁定該 step 的 required artifact targets，但只移除 run directory 內的目標；optional artifacts 和外部絕對路徑不會被清除。

### 驗證類型與專用欄位

| `type` | 檢查用途 | 專用欄位 | 範例 |
| --- | --- | --- | --- |
| `exists` | 檢查路徑存在；檔案或目錄皆可 | 無 | `path: result.csv` |
| `file_size` | 檢查檔案大小是否在界限內 | min_size_bytes、max_size_bytes | `min_size_bytes: 100` |
| `file_extension` | 檢查最後一段副檔名 | allowed_extensions | `allowed_extensions: [.csv, .txt]` |
| `directory_not_empty` | 檢查目錄至少有一個直接子項目 | 無 | `path: logs` |
| `csv_content` | 檢查 CSV header、必要欄位與資料列數 | required_columns、min_rows | `min_rows: 2` |
| `json_content` | 檢查 JSON 能解析、必要 key 路徑與值 | required_json_paths、expected_json_values | `required_json_paths: [summary.status]` |

未知 type 會產生 ARTIFACT_INVALID 驗證結果，不是新的驗證插件。CSV 檢查列數與 header，不驗證每格資料是否為數字。JSON 路徑是以 `.` 分隔的物件 key，不是 JSONPath；不支援陣列索引。

| 變數名稱 | 必填／選填 | 型別與預設值 | 意義與用途 | 範例 |
| --- | --- | --- | --- | --- |
| `rules[].min_size_bytes` | 選填；file_size 使用 | 整數；`null` | 最小 bytes，等於下限可通過 | `100` |
| `rules[].max_size_bytes` | 選填；file_size 使用 | 整數；`null` | 最大 bytes，等於上限可通過 | `1048576` |
| `rules[].allowed_extensions` | 載入時選填；file_extension 驗證需非空 | 字串 list；`[]` | 允許的副檔名；忽略大小寫，省略開頭的點也可 | `[csv, .json]` |
| `rules[].required_columns` | 選填；csv_content 使用 | 字串 list；`[]` | CSV 必須包含的欄位，名稱區分大小寫；實際 header 會去掉兩側空白 | `[timestamp, power]` |
| `rules[].min_rows` | 選填；csv_content 使用 | 整數；`null` | 最少資料列數，不含 header | `2` |
| `rules[].required_json_paths` | 選填；json_content 使用 | 字串 list；`[]` | 必須存在的物件 key 路徑；值為 null 仍算存在 | `[summary.status]` |
| `rules[].expected_json_values` | 選填；json_content 使用 | mapping；`{}` | 路徑與預期值；使用 Python 相等比較，不做嚴格 schema 型別驗證 | `{summary.status: PASSED}` |

file_extension 必須提供非空 allowed_extensions 才能通過驗證；省略或空清單會產生 ARTIFACT_INVALID。file_size 省略兩個界限時只檢查檔案是否存在且為檔案。CSV 即使省略 required_columns 仍需有 header；JSON 即使省略專用欄位仍需可解析。

以下片段需放入完整 YAML 的 artifact 區塊；假設腳本會產生這些檔案：

```yaml
artifact:
  output_dir: artifacts
  validation:
    rules:
      - name: power_csv
        type: csv_content
        path: results/power.csv
        after_step: measure_power
        required_columns: [timestamp, power]
        min_rows: 2
      - name: summary_json
        type: json_content
        path: summary.json
        required_json_paths: [summary.status]
        expected_json_values:
          summary.status: PASSED
      - name: debug_log
        type: file_size
        path: debug.log
        required: false
        min_size_bytes: 1
```

## 路徑與環境變數

命令繼承啟動 runner 的環境變數，executor 另外設定下表中的兩個值。它們是 subprocess 的環境變數，不是 YAML 設定欄位。

| 變數名稱 | 必填／選填 | 意義與用途 | 範例 |
| --- | --- | --- | --- |
| `DEVICE_TEST_RUNNER_ROOT` | 自動提供；不需填入 YAML | CLI 使用專案根目錄；Python API 使用 executor.project_directory | `bash "$DEVICE_TEST_RUNNER_ROOT/scripts/test.sh"` |
| `RUN_ARTIFACT_DIR` | 自動提供；不需填入 YAML | 當次 run directory 的絕對路徑 | `echo "$RUN_ARTIFACT_DIR"` |

CLI 的 --config 和相對 artifact.output_dir 以啟動命令時的工作目錄為基準。step command 的工作目錄則是 run directory；artifact rule 的相對 path 也以 run directory 為基準，絕對 path 直接使用原位置。

目前不支援 YAML `variables`、自訂 run／step environment mapping 或 `${vars.name}`／`${context.name}` 替換。`$DEVICE_TEST_RUNNER_ROOT` 等值由 shell 展開，引用路徑時加上雙引號。`device.serial` 不會自動成為 subprocess environment。

## CLI 與結果判讀

在專案根目錄執行 `poetry run python main.py --config configs/hello.yaml`。

| 參數名稱 | 必填／選填 | 意義與用途 | 範例 |
| --- | --- | --- | --- |
| `--config` | 必填 | YAML 路徑；相對於啟動工作目錄 | `--config configs/hello.yaml` |
| `-h`／`--help` | 選填 | 顯示 argparse 提供的使用說明 | `python main.py --help` |

| `summary.status` | 意義 | CLI exit code |
| --- | --- | --- |
| `PASSED` | 所有影響結果的工作與規則通過 | `0` |
| `FAILED` | cleanup、step、skipped step 或 required artifact 失敗 | `1` |
| `CANCELLED` | 使用者取消或取消的 steps | `130` |
| `TIMED_OUT` | run scope 到期 | 目前為 `0`；自動化需讀取 status |

設定載入失敗或未處理例外不一定產生 result.json。第一次 Ctrl+C 請求取消並進入受控清理；第二次可中斷清理與報告。SIGTERM 未接到取消 token。

### Failure type 參考

| 值 | 意義與用途 | 常見例子 |
| --- | --- | --- |
| `none` | 沒有失敗 | 命令與影響結果的驗證通過 |
| `cancelled` | attempt 被 token 中止 | 使用者取消、run 或 cleanup scope timeout |
| `timeout` | Step attempt 超過 timeout_second | 等待裝置回應過久 |
| `device_offline` | 失敗訊息包含裝置不可用文字 | `device offline`、`device unauthorized` |
| `process_error` | 其他程序失敗 | 非零 exit code、指令不存在 |
| `artifact_missing` | 驗證目標不存在 | 未產生 result.csv |
| `artifact_invalid` | 驗證內容或目標型態不符 | CSV 列數不足、JSON 值不符 |

裝置離線分類來自失敗時的 stderr／error 文字，不會主動探測裝置。可辨識文字還包含 `no devices/emulators found` 和 `device not found`。程序失敗時優先看 step timeout，再看離線文字，其餘歸為 process_error。

### 報告欄位

報告欄位是 runner 輸出，不需要填入 YAML。下表列出判讀用途；完整資料形狀見 [報告範例](#報告範例)。

| 欄位名稱 | 意義與用途 | 範例 |
| --- | --- | --- |
| `metadata` | 測試／裝置資訊、runner_version、UTC started_at／finished_at 與取消資訊 | `cancel_reason: run_timeout` |
| `metadata.cancel_requested` | run token 是否已取消；不是 cleanup token | `true` |
| `metadata.cancel_reason` | 第一個 run 取消原因；未取消為 null | `user_request` |
| `metadata.run_timeout_seconds`／`run_timed_out` | run 預算與是否由 run timeout 取消 | `3600`／`true` |
| `summary.status` | 自動化判斷 run 成敗的依據 | `TIMED_OUT` |
| `summary.configured_steps`／`executed_steps` | 設定步驟數與已記錄 StepResult 數；後者不等於 subprocess 次數 | `6`／`4` |
| `summary.passed_steps`／`failed_steps`／`cancelled_steps`／`skipped_steps` | 步驟結果計數；skipped 為設定數減已記錄數 | `cancelled_steps: 1` |
| `summary.configured_artifact_rules`／`passed_artifact_rules`／`failed_artifact_rules`／`failed_required_artifact_rules` | Final validation 規則計數；optional 失敗也計入 failed_artifact_rules | `failed_required_artifact_rules: 1` |
| `summary.duration_seconds` | 包含 cleanup、final validation 與結果建構前工作的耗時；不含報告寫入 | `2.5` |
| `cleanup_summary.attempted` | 已進入 cleanup 路由，空階段也可能為 true | `true` |
| `cleanup_summary.timed_out`／`failed`／`cancellation_reason` | Cleanup 整體逾時、失敗與自己的取消原因 | `cleanup_timeout` |
| `step_results[]` | stage、name、command、attempts、success、cancelled、duration_seconds 與 attempt_results | `attempts: 2` |
| `step_results[].attempt_results[]` | 每次 attempt 的 success、failure_type、timed_out、cancelled、exit_code、duration_seconds、stdout／stderr、log 路徑、error 與 artifact_validation_results | `failure_type: timeout` |
| `artifact_validation_results[]` | Final validation 的 name、type、path、passed、required、failure_type、message、actual_size_bytes | `failure_type: artifact_invalid` |
| `artifact_dir` | 當次 run directory | `artifacts/hello_<timestamp>` |

`timed_out` 在 attempt 上只表示 step timeout；run／cleanup timeout 中止程序時 attempt 是 cancelled。artifact failure 不會改寫原始取消原因。metadata 沒有 cleanup_timeout_seconds，清理結果請讀 cleanup_summary。

## 透過 Python API 取消

CLI 第一次 Ctrl+C／SIGINT 會呼叫 `token.cancel()`；第二次會拋出 `KeyboardInterrupt`，可能中斷 cleanup 與報告寫入。CLI 正常完成回傳 0、FAILED 回傳 1、CANCELLED 或 run 期間的 KeyboardInterrupt 回傳 130。SIGTERM 尚未接到 token。

Python API 由呼叫端持有 token 並呼叫 `cancel()`。以下示範沿用載入的 configuration，在兩秒後提出取消請求：

```python
from pathlib import Path
from threading import Timer

from runner.artifact import ArtifactManager
from runner.artifact_validator import ArtifactValidator
from runner.cancellation import CancellationToken
from runner.config import ConfigLoader
from runner.executor import SubprocessExecutor
from runner.failure import FailureClassifier
from runner.process import ProcessTerminator
from runner.reporter import JsonReporter
from runner.runner import DeviceTestRunner

config = ConfigLoader().load("configs/sample.yaml")
classifier = FailureClassifier()
runner = DeviceTestRunner(
    executor=SubprocessExecutor(
        project_directory=Path.cwd(),
        failure_classifier=classifier,
        process_terminator=ProcessTerminator(),
    ),
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

Executor 每 0.1 秒檢查取消與 timeout。每次 attempt 建立獨立 session，清理時對 process group 送 SIGTERM，預設等待 2 秒；仍有程序則送 SIGKILL，再等最多 2 秒。stdout／stderr reader 各有 2 秒 join 上限。上述 timer 不是兩秒內返回的保證。

同群組的 child／grandchild 已有清理測試；自行脫離群組的程序，以及直接 process 正常退出後留下的背景程序，不在目前保證內。詳見 [Process Lifecycle](process_lifecycle.md)。Cancelled attempt 不做 attempt validation 或 retry，但 run 最後仍驗證所有 artifacts。

## 設定整次執行逾時

在 YAML 頂層設定：

```yaml
run_timeout_seconds: 3600
```

省略或 null 代表不設 run deadline；step 的 `timeout_second` 仍有效。只接受有限正數，拒絕 bool、字串、零、負數、NaN 與 Infinity。Deadline 在 global_setup 前啟動，不隨 retry 重設。

Run timeout 透過 cancellation 停止一般工作，report 為 `TIMED_OUT`、`cancel_reason: run_timeout`。被中斷的 attempt 仍是 CANCELLED，`timed_out` 專指 step timeout。Retry delay 中逾時會保留前一次失敗，不新增 attempt。第一個取消原因不會被後續請求覆寫。

Run watchdog 在一般工作結束後停止。Cleanup 共用獨立 token、自己的整體 deadline 與各 step timeout；final validation 在 cleanup 後執行，不受兩個 scope 的 deadline 中斷，因此不保證 CLI 在設定秒數內返回。`metadata.run_timed_out` 在取消原因為 RUN_TIMEOUT 時是 `true`。CLI 目前沒有 TIMED_OUT 專用非零 exit code，會回傳 0；自動化應檢查 `summary.status`。

## 設定清理逾時

```yaml
cleanup_timeout_seconds: 60
```

省略或 null 代表不設 cleanup 整體 deadline；YAML 值必須是有限正數。teardown、global_teardown 的 attempts 與 retry delays 共用此預算，各 step 的 `timeout_second` 仍有效。一般 cleanup step 失敗會繼續後續清理；整體 deadline 到期則中止目前程序並停止啟動新步驟。

報告的 `cleanup_summary` 保存 `attempted`、`timed_out`、`failed` 與 `cancellation_reason`；`attempted` 表示已進入 cleanup stage 路由，空 steps 也可能為 true。`cleanup_timeout_seconds` 不寫入 metadata。原始 run timeout／使用者取消優先於 cleanup failure 與 artifact failure；沒有 run cancellation 時，cleanup failure 使 status 為 FAILED。詳見 [Cancellation-Aware Cleanup](cancellation_aware_cleanup.md)。

## 輸出檔案

每次測試執行會建立獨立的 run directory。

範例：

```text
artifacts/
└── power_idle_test_2026_07_22_22_30_00/
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
    "runner_version": "1.6.3",
    "started_at": "2026-09-12T00:00:00+00:00",
    "finished_at": "2026-09-12T00:00:01+00:00",
    "cancel_requested": false,
    "cancel_reason": null,
    "run_timeout_seconds": null,
    "run_timed_out": false
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
  "cleanup_summary": {
    "attempted": true,
    "timed_out": false,
    "failed": false,
    "cancellation_reason": null
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

結果消費端應以 `summary.status` 判斷 run；Python API 的 `RunResult.passed` 只於 status 為 `PASSED` 時回傳 true。單次 attempt 請讀取 `success`、`failure_type`、`timed_out` 與 `cancelled`。
