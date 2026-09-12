# Device Test Runner Architecture v1.6.0 — Cancellation Foundation

## 1. 版本定位與證據

v1.6.0 在 v1.5.3 的 selective retry 與 artifact criticality 上加入 cooperative cancellation。`DeviceTestRunner.VERSION` 為 `1.6.0`；呼叫端可傳入 `CancellationToken`，在一般 lifecycle step 或 retry delay 期間要求取消。

本文件以 Git tag `v1.5.3` 為比較基準，依據目前 `runner/`、`tests/`、`configs/` 的變更描述 v1.6.0；目標 tag `v1.6.0` 尚待建立。這是 cancellation foundation，不代表完整 process-tree、signal 或 exception cleanup guarantees 已完成。

## 2. Components and Data Flow

```mermaid
flowchart TD
    C[ConfigLoader / RunnerConfig] --> R[DeviceTestRunner]
    T[Caller / CancellationToken] --> R
    T --> E[SubprocessExecutor]
    R --> E
    E --> L[Per-attempt stdout / stderr logs]
    E --> A{Attempt cancelled?}
    A -- Yes --> X[Stop step and skip attempt validation]
    A -- No --> V[Validate bound rules after process success]
    V --> P[FailureClassifier / RetryPolicy]
    P --> W[Required target cleanup / cancellable delay]
    W --> R
    X --> G[Reachable teardown / global_teardown]
    G --> F[Final validation of all rules]
    F --> J[RunResult / JsonReporter]
```

* `CancellationToken` 使用 `threading.Event`；`cancel()` 可重複呼叫，`is_cancelled` 回報狀態，`raise_if_cancelled()` 在取消後拋出 `CancellationRequested`。Runner 本身以狀態檢查實作流程，不使用該例外路徑。
* `run(config, cancellation_token=None)` 未收到 token 時建立新 token。一般 stage 與 attempt 開始前檢查取消，避免繼續啟動工作。
* Cleanup attempt 使用新的未取消 token，避免外部已取消的 token 立刻終止清理程序。

## 3. Executor and Retry

Executor 使用 `shell=True` 在 run directory 執行 command，設定 `DEVICE_TEST_RUNNER_ROOT` 與 `RUN_ARTIFACT_DIR`，由兩個 thread 讀取 stdout／stderr。

每輪最多等待 0.1 秒，依序檢查 process completion、token cancellation、step timeout。已觀察到程序完成時先結束 polling；若仍執行中且取消與 timeout 同時可見，取消優先。取消回傳 `failure_type=cancelled`、`cancelled=true`、`timed_out=false`；timeout 回傳 `failure_type=timeout`、`timed_out=true`、`cancelled=false`。

`_stop_process()` 對直接 `Popen` 程序送出 terminate，等待最多兩秒，仍未退出才 kill 並 wait。接著等待輸出 reader 結束並保存已讀取的 log。這不是總執行時間上限：未被終止的後代程序可能繼續持有 pipe，使 reader join 延遲。

取消 attempt 不執行 attempt-level artifact validation，也不重試。一般成功 command 才驗證 `after_step` 綁定規則；process failure 優先於 required artifact failure，optional artifact 僅供診斷。允許重試時，只清除 run directory 內的 required targets。

Retry delay 使用 monotonic clock，以最多 0.1 秒的 sleep 檢查取消。若等待中取消，step 標記 `cancelled=true`，但已完成 attempt 保留原始 failure type。Cleanup 使用原始 token 等待 retry delay，因此取消後可以略過剩餘 delay 並繼續 cleanup retry；不保證取消後 cleanup 仍等待完整設定時間。

## 4. Lifecycle Routing

| 取消時機 | 後續行為 |
| --- | --- |
| run 開始前 | 只執行 `global_teardown`，一般 steps 算 skipped，可能沒有 cancelled step |
| `global_setup` 執行中 | 停止該 stage，跳過 `setup`、`scenario`、`teardown`，執行 `global_teardown` |
| 進入 `setup` 區塊後，於 `setup` 或 `scenario` 取消 | 停止一般工作，執行 `teardown` 與 `global_teardown` |
| 一般 step 的 retry delay | 不啟動下一次 attempt，依 stage 路由至 cleanup |
| cleanup 執行期間 | 新的 execution token 不受原始取消狀態影響，仍受各 step timeout 與 retry policy 控制 |

`teardown` 實際位於 `global_setup_success and not cancellation_token.is_cancelled` 區塊內；如果 global_setup 完成後、進入該區塊前就觀察到取消，teardown 會被跳過。`global_teardown` 是受控流程中的 best effort，程式沒有以 `try/finally` 包覆整個 run；未處理的 Python exception 或 KeyboardInterrupt 不在此保證內。

Lifecycle 後仍對 **所有** artifact rules 做 final validation，包括有 `after_step` 的規則與被取消／跳過 step 的規則。因此取消 run 可以同時包含 missing required artifact 診斷。

## 5. Report Contract and Compatibility

| 層級 | v1.6.0 欄位／行為 |
| --- | --- |
| `StepAttemptResult` | 新增必要建構參數 `timed_out`、`cancelled`；取消 failure type 為 `cancelled` |
| `StepResult` | 新增必要建構參數 `cancelled`；retry delay 取消也可使此欄位為 true |
| `RunMetadata` | `runner_version=1.6.0`，新增必要參數 `cancel_requested` |
| `ExecutionSummary` | 新增必要參數 `cancelled_steps`；`failed_steps` 排除 cancelled steps |
| `SubprocessExecutor.execute` | 呼叫端與 mock executor 必須提供 `cancellation_token` |
| `DeviceTestRunner.run` | token 為 optional，既有 `run(config)` 呼叫形式仍可使用 |

`executed_steps = len(step_results)`，`skipped_steps = configured_steps - executed_steps`。Summary status 優先序：取消請求或 cancelled step → `CANCELLED`；否則 failed step、skipped step、required artifact failure 任一存在 → `FAILED`；其餘 → `PASSED`。`cancel_requested` 與 `cancelled_steps` 不等價，例如執行前取消的 run 可為 `true`／`0`。

結果消費端應讀取 `summary.status` 與 attempt `success`。目前 `RunResult.passed` 只檢查 step success，`StepAttemptResult.passed` 只檢查 exit code；兩者不等同包含取消與 artifact 判定的完整結果。

YAML 禁止 `retry_on: [cancelled]`，policy 即使收到直接 Python 建構且包含 `CANCELLED` 的清單也不重試。YAML 未指定 `retry_on` 時為空清單；直接 `RetryConfig()` 的預設包含五種一般 failure types，預設 `max_attempts=1`。呼叫端宜明確指定 retry policy。

## 6. Remaining Work

* Process-group／descendant termination 與可量測的 shutdown 上限。
* CLI SIGINT／SIGTERM 接線與明確 exit code 策略。
* 未處理例外時的 teardown／report finalization。
* Cancellation boundary race 與 cleanup retry-delay semantics 的更完整測試。
* Sample happy path 修正、release tag 與 GitHub Release 驗證。
