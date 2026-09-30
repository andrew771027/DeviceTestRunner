# Device Test Runner v1.6.2 Test Matrix

Version scope: Run-level Timeout. Evidence is the working tree based on `eea8507`, compared with tag `v1.6.1`; release publication is unverified.

## Requirement coverage

Unit paths are under `tests/test_unit/`; integration paths under `tests/test_integration/`. A test in the unit directory can still launch a real process.

| Area | Scenario | Level | Test | Assertion / boundary |
| --- | --- | --- | --- | --- |
| Configuration | Missing timeout → unlimited | Unit / YAML | `test_config_loader.py::test_missing_run_timeout_defaults_to_unlimited` | None；不啟動 watchdog 的 runner 行為由程式核對 |
| Configuration | Zero / negative / non-finite rejected | Unit / parser | `test_config_loader.py::test_run_timeout_must_be_finite_and_positive` | 0、負數、NaN、±Infinity 拋 ValueError |
| Configuration | Boolean rejected | Unit / parser | `test_config_loader.py::test_run_timeout_rejects_boolean` | 拒絕 bool |
| Cancellation | First reason preserved | Unit | `test_cancellation.py::test_first_cancellation_reason_wins` | USER_REQUEST 不被 RUN_TIMEOUT 覆寫 |
| Cancellation | RUN_TIMEOUT recorded | Unit | `test_cancellation.py::test_run_timeout_reason_cannot_be_overwritten_by_user_cancel` | 反方向也保留第一個原因 |
| Watchdog | Deadline cancellation | Unit / real thread | `test_run_timeout.py::test_watchdog_requests_cancellation_on_timeout` | 限時輪詢確認 RUN_TIMEOUT |
| Watchdog | Stop prevents cancellation | Unit / real thread | `test_run_timeout.py::test_watchdog_stop_prevents_timeout` | stop 返回後 token 未取消且 thread 已停止；未另外等待超過原期限 |
| Watchdog | User reason survives deadline | Unit / real thread | `test_run_timeout.py::test_watchdog_does_not_overwrite_existing_cancellation_reason` | deadline 後仍為 USER_REQUEST |
| Executor | Interrupt long-running process | Integration | `test_integration_run_timeout_executor.py::test_run_timeout_cancels_running_executor` | CANCELLED、timed_out=false、保留 stdout，耗時小於 10 秒 |
| Executor | Step timeout remains TIMEOUT | Unit / Mock | `test_executor.py::test_subprocess_executor_raised_timeout_error` | TIMEOUT、timed_out=true、cancelled=false |
| Runner / Lifecycle | No retry; skip remaining steps; cleanup | Integration | `test_integration_runner_timeout.py::test_run_timout_stops_retry_and_runs_cleanup` | 一次 attempt、後續 step 未執行、cleanup marker 存在 |
| Runner / Reporting | Timeout during retry delay | Integration | `test_integration_runner_timeout.py::test_run_timeout_during_retry_delay` | 只留一筆 PROCESS_ERROR；step cancelled、run TIMED_OUT |
| Lifecycle | Timeout during setup | Integration | `test_integration_runner_timeout.py::test_run_timeout_during_setup_runs_cleanup` | 不跑 scenario，teardown 與 global_teardown 執行 |
| Runner | Timeout between steps | Unit / fake executor | `test_runner.py::test_run_timeout_between_steps_stops_next_step` | 第一步成功仍保存，下一步不執行；未使用真實 watchdog |
| Reporting | Status precedence | Unit / parameterized | `test_run_status.py::test_run_status_matrix` | 無取消原因時，failed／cancelled／skipped／artifact counts 的狀態；原因優先順序另由同檔測試驗證 |
| Process | Reaped child with live descendant | Unit directory / real process | `test_process.py::test_terminator_cleans_group_even_when_direct_child_has_exited` | 原 process group 被清理 |

The two runner timeout/retry integration tests also read `result.json`: status, cancellation reason, configured timeout, one attempt, original failure type and flags are asserted. They also assert `metadata.run_timed_out` is true; the reporter unit test asserts its default is false. General reporter tests compare serialized dataclasses, but do not replace run-timeout-specific assertions.

## AI 協作案例與修正

以下來源依本次對話紀錄確認；其他案例不推測作者。

| 原本缺口／失敗 | 修改 | 防止回歸的測試 | 限制 |
| --- | --- | --- | --- |
| 省略 timeout 被數字型別檢查拒絕 | loader 遇 None 直接回傳 | `test_missing_run_timeout_defaults_to_unlimited` | 未單獨驗證 null YAML |
| 非有限值缺少測試證據 | 加入 NaN、±Infinity、零與負數參數化 | `test_run_timeout_must_be_finite_and_positive` | 直接 RunnerConfig 不經 loader |
| 報告只檢查記憶體結果 | 兩個 runner integration tests 讀取 JSON 與 attempt flags | timeout during command／retry delay tests above | 尚未驗證 CLI exit code |
| `Event.eait` 拼字使 thread 崩潰 | 改用 Event.wait | `test_watchdog_requests_cancellation_on_timeout` | 排程時間不是精確即時保證 |
| 不存在 artifact 被分類 INVALID | exists 改為 MISSING | `test_exists_rule_fails_when_file_missing`、`test_validate_all_returns_all_results` | 空目錄仍是 INVALID |
| 大小訊息包含縮排空白 | 相鄰字串拼接 | `test_file_size_rule_fails_below_minimum`／`test_file_size_rule_fails_above_maximum` | 僅修正診斷格式 |
| 空目錄測試誤認 MISSING | 改為 INVALID 預期 | `test_directory_not_empty_fails_when_empty` | 路徑存在但內容不合規 |
| fixture root 少上一層、import／屬性／步驟名稱錯誤 | 修正測試準備與斷言 | setup timeout、orphan、executor 與 runner timeout tests | 測試錯誤與產品問題分開處理 |
| direct child 結束即跳過 group cleanup | 探測原 group 並清理 descendants | orphan test above；`test_terminated_process_does_not_need_cleanup` | 不涵蓋 detached child |
| status 參數用無序 set | 改用 tuple | `test_run_status_from_cancellation_reason` | 避免資料順序不穩定 |

本次文件更新只補測試 docstring，不修改可執行行為。寫法見 [測試指南 v1.6.2](../test_guide.md#v1-6-2)，實際命令與結果見 [完成條件](../definition_of_done/definition_of_done_v1.6.2.md)。

## 尚未覆蓋

- 多個真實短 steps 累計觸發 deadline；目前 between-steps 用 fake executor 注入原因。
- deadline 正好與 stop、process completion、user cancellation 同時發生的競態。
- cleanup 或 final validation 期間首次觸發 timeout、例外後 report finalization。
- CLI TIMED_OUT exit code、Linux CI、detached descendants 與所有正常退出後殘留背景程序的路徑。

## 命令組合的閱讀入口

Timeout cleanup 測試以 `shlex.quote()` 保留 shell 參數，以 `repr(str(marker))` 產生內嵌 Python 路徑常值。兩層解析、逐步範例與不經 shell 的替代寫法見 [測試指南：命令引用](../test_guide.md#v1-6-2-command-quoting)。現有測試未專門參數化含特殊字元的路徑；教學範例不計入測試案例數。
