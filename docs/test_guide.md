# Pytest 測試指南

本文件說明 Device Test Runner 測試使用的 pytest 工具、fixture 與模擬方式。先從用法大綱找到需要的工具，再看各版本的實際案例。測試覆蓋哪些需求、重要修正與驗證結果，仍記錄在各版 [test matrix](test_matrix/)。

## 閱讀大綱

1. [工具與用法](#tools)：fixture、函式、decorator、Mock／Fake 與執行指令。
2. [Fixture 與輔助腳本](#fixtures)：區分 pytest 提供的資源與測試自行啟動的腳本。
3. [常用寫法](#usage)：共用語法與執行方式。
4. [版本索引](#versions)：對照各版實際使用方式與來源。

<a id="tools"></a>

## 工具與用法

下表提供閱讀入口，不表示每一版都使用全部工具。版本細節見後面的案例；教學範例不算新增測試。

| 工具／寫法 | 類型 | 用途 | 本專案的閱讀入口 |
| --- | --- | --- | --- |
| `assert` | Python 語法 | 比較實際與預期結果；pytest 顯示失敗位置與差異 | [v1.0.0](#v1-0-0) 起的案例 |
| `tmp_path` | Pytest 內建 fixture | 提供每個案例自己的暫存目錄 | [v1.0.0](#v1-0-0) |
| `monkeypatch`、`setattr()` | 內建 fixture 與方法 | 暫時替換函式／屬性，結束後還原 | [v1.2.0](#v1-2-0) |
| `unittest.mock.Mock` | Python 標準函式庫 | 建立可設定結果與記錄呼叫的假物件；不是 pytest fixture | [v1.2.0](#v1-2-0) |
| Fake／測試 helper | 專案自訂類別或函式 | 用簡單實作模擬依賴，或準備共用資料 | [v1.6.1](#v1-6-1) 的 FakeProcess |
| `@pytest.mark.parametrize` | Decorator | 同一段測試用不同資料執行 | [v1.0.0](#v1-0-0) |
| `capsys`、`readouterr()` | 內建 fixture 與方法 | 擷取 console 的 stdout／stderr | [v1.3.5](#v1-3-5) |
| `pytest.raises()` | 例外檢查工具 | 驗證操作拋出指定例外 | [v1.2.0](#v1-2-0)；[v1.6.1](#v1-6-1) 的 KeyboardInterrupt |
| `shlex.quote()`、`repr()` | 標準函式庫／內建函式 | 分別處理 shell 參數與 Python 字串常值 | [v1.6.2 命令引用](#v1-6-2-command-quoting) |
| 模擬時鐘 | 測試技巧 | 由測試推進時間，不必真的等待 | [v1.6.0](#v1-6-0) |
| `pytest.approx()` | 比較工具 | 容許浮點數計算的小誤差 | [v1.6.0](#v1-6-0) |
| `@pytest.mark.retry` 等 | 自訂 marker | 將測試分類，方便選擇執行 | [v1.5.0](#v1-5-0) |
| `-m`、`-k`、`檔案::函式` | 執行選項 | 分別依 marker、名稱或指定函式選擇測試 | 各版本的「執行與定位案例」 |
| `-q`、`-v` | 輸出選項 | 顯示精簡結果或逐一列出案例 | 各版本的執行範例 |

本版新增案例也使用 `json.loads` 讀取落盤報告，以及 `time.monotonic` 搭配有上限的輪詢；兩者是標準函式庫，不是 pytest fixture。見 [v1.6.2](#v1-6-2)。

<a id="fixtures"></a>

## Fixture 與輔助腳本

Pytest fixture 是 pytest 準備後交給測試的資源。測試參數中的 `tmp_path`、`monkeypatch` 與 `capsys` 都是內建 fixture；不需要自己宣告 `@pytest.fixture`。

`@pytest.fixture` 用來定義自訂 fixture。目前 executor、reporter 等測試使用此 decorator 準備輸入與預期資料。一般 helper 函式需要由程式呼叫，不會因為名稱有 mock 就自動注入測試。

`tests/fixtures/` 則是專案放置輔助腳本的資料夾。v1.6.1 的 `process_tree.py` 與 `retry_process.py` 由 subprocess 執行，並不是 pytest 自動注入的 fixture。詳細流程見 [v1.6.1](#v1-6-1)。

<a id="usage"></a>

## 常用寫法

以下是語法示例，不是新增的專案測試。各版實際案例見後面的版本章節。

### 暫存目錄與參數化

Pytest 依參數名稱提供 `tmp_path`。`tmp_path: Path` 的型別標註只幫助閱讀，不負責提供資源。

```python
def test_write_output(tmp_path):
    output_file = tmp_path / "output.txt"
    output_file.write_text("done", encoding="utf-8")
    assert output_file.read_text(encoding="utf-8") == "done"
```

`parametrize` 每列資料執行一次案例。資料參數不是內建 fixture；函式數也不一定等於案例數。

```python
import pytest

@pytest.mark.parametrize(
    argnames="exit_code, expected_success",
    argvalues=[(0, True), (1, False)],
)
def test_exit_code_example(exit_code, expected_success):
    assert (exit_code == 0) is expected_success
```

### 替換函式與模擬依賴

`monkeypatch` 是 fixture，`setattr()` 是它的方法。替換的是程式查找函式的位置，測試結束後會自動還原。

```python
monkeypatch.setattr(module_object, "function_name", fake_function)
monkeypatch.setattr("package.module.function_name", fake_function)
```

以上名稱需換成實際物件或路徑。假函式必須接受正式呼叫使用的參數。

Mock 建立可設定回傳值、例外與呼叫紀錄的假物件；monkeypatch 將程式使用的位置換成它。也可以用一般函式、簡單類別與 list，像 v1.6.1 的 `FakeProcess`。

若替換函式先記錄物件，再呼叫原本函式，測試仍會執行真實操作。因此使用 monkeypatch 不等於完全模擬 OS 行為。

### 輸出、例外與時間

| 工具 | 寫法與檢查方式 |
| --- | --- |
| `capsys` | `captured = capsys.readouterr()` 後檢查 `captured.out`／`captured.err`；log 檔案另以 `read_text()` 驗證 |
| `pytest.raises` | `with pytest.raises(ExpectedError):` 的區塊必須拋出指定例外，沒有拋出就失敗 |
| 模擬 sleep | 假函式記錄等待秒數，不真的睡眠；適合檢查單次等待請求 |
| 模擬時鐘 | 同時替換 sleep 與 clock，讓假 sleep 推進時間，clock 回傳新值；適合 deadline／polling 測試 |
| `pytest.approx` | 比較浮點值是否足夠接近，避免把多次 0.1 秒累加的精度誤差當成失敗 |

### 選擇測試與閱讀結果

在對應版本的 checkout、已安裝依賴的環境執行：

```bash
python -m pytest -q
python -m pytest path/to/test_file.py::test_function -v
python -m pytest -m retry -v
python -m pytest -k timeout -v
```

第二行的路徑與函式需換成實際案例。`-m` 依 marker 分類篩選，`-k` 依名稱等關鍵字篩選，`-q` 精簡輸出，`-v` 列出各案例。指定參數化函式時，會執行其所有資料列。

不是每個 retry 測試都有 `retry` marker。完整功能驗證應依 test matrix 選擇相關檔案或跑完整 suite。

<a id="versions"></a>

## 版本索引

舊版依對應 Git tag 的測試說明；開發中版本依該節記錄的 source 基準。路徑或介面可能隨版本改變，請勿直接用目前程式推論舊版行為。本次搬移文件沒有重新執行歷史測試。

| 版本 | 閱讀重點 | 測試覆蓋與證據 |
| --- | --- | --- |
| [v1.6.2](#v1-6-2) | Watchdog、設定邊界、JSON attempt history、orphan process | [Test matrix](test_matrix/test_matrix_v1.6.2.md) |
| [v1.0.0](#v1-0-0) | tmp_path、參數化與基本斷言 | [Test matrix](test_matrix/test_matrix_v1.0.0.md) |
| [v1.1.0](#v1-1-0) | 模型更名後的案例與參數化 | [Test matrix](test_matrix/test_matrix_v1.1.0.md) |
| [v1.2.0](#v1-2-0) | monkeypatch.setattr、Mock、TimeoutExpired | [Test matrix](test_matrix/test_matrix_v1.2.0.md) |
| [v1.3.0](#v1-3-0) | Lifecycle 與 artifact 測試的準備資料 | [Test matrix](test_matrix/test_matrix_v1.3.0.md) |
| [v1.3.5](#v1-3-5) | capsys 與輸出串流測試 | [Test matrix](test_matrix/test_matrix_v1.3.5.md) |
| [v1.4.0](#v1-4-0) | Artifact validation 的檔案隔離 | [Test matrix](test_matrix/test_matrix_v1.4.0.md) |
| [v1.4.1](#v1-4-1) | CSV／JSON 驗證案例與既有 pytest 工具 | [Test matrix](test_matrix/test_matrix_v1.4.1.md) |
| [v1.5.0](#v1-5-0) | Retry marker、pytest.raises 與替換 sleep | [Test matrix](test_matrix/test_matrix_v1.5.0.md) |
| [v1.5.1](#v1-5-1) | Artifact-aware retry 的分類與案例路徑 | [Test matrix](test_matrix/test_matrix_v1.5.1.md) |
| [v1.5.2](#v1-5-2) | Failure classification 的測試用法 | [Test matrix](test_matrix/test_matrix_v1.5.2.md) |
| [v1.5.3](#v1-5-3) | Selective retry 與設定錯誤測試 | [Test matrix](test_matrix/test_matrix_v1.5.3.md) |
| [v1.6.0](#v1-6-0) | 模擬時鐘、pytest.approx 與取消測試 | [Test matrix](test_matrix/test_matrix_v1.6.0.md) |
| [v1.6.1](#v1-6-1) | Process fixture 腳本、FakeProcess、四組參數與 SIGINT | [Test matrix](test_matrix/test_matrix_v1.6.1.md) |


<a id="v1-0-0"></a>

## v1.0.0

依據 Git tag `v1.0.0`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.0.0.md)。

本版沿用暫存目錄與參數化，使用方式見上方「常用寫法」。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_config_loader.py::test_config_loader_loads_yaml` | tmp_path |
| `tests/test_runner.py::test_runner_runs_single_scenario` | 參數化／測試資料準備 |

<a id="v1-1-0"></a>

## v1.1.0

依據 Git tag `v1.1.0`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.1.0.md)。

本版沿用暫存目錄與參數化，使用方式見上方「常用寫法」。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_contract_config_yaml.py::test_config_yaml_contract` | tmp_path |
| `tests/test_command_executor.py::test_command_step_executor_success` | 參數化／測試資料準備 |

<a id="v1-2-0"></a>

## v1.2.0

依據 Git tag `v1.2.0`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.2.0.md)。

本版 executor 測試使用 `monkeypatch.setattr(subprocess, "run", ...)`，替換 `subprocess.run`。成功案例回傳準備好的 `CompletedProcess`；逾時案例由假函式拋出 `TimeoutExpired`，不用真的等命令逾時。

本版 timeout 測試預期 `subprocess.TimeoutExpired` 往外拋。後續版本改成回傳失敗結果，因此不要把這個舊版預期直接套到新版 executor。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_config_loader.py::test_config_loader_loads_device_test_config` | tmp_path |
| `tests/test_executor.py::test_subprocess_executor_passes_timeout_to_subprocess` | monkeypatch、Mock |
| `tests/test_executor.py::test_subprocess_executor_return_success` | 參數化／測試資料準備 |
| `tests/test_executor.py::test_subprocess_executor_raised_timeout_error` | 參數化／測試資料準備 |

<a id="v1-3-0"></a>

## v1.3.0

依據 Git tag `v1.3.0`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.3.0.md)。

本版 executor 測試使用 `monkeypatch.setattr(subprocess, "run", ...)`，替換 `subprocess.run`。成功案例回傳準備好的 `CompletedProcess`；逾時案例由假函式拋出 `TimeoutExpired`，不用真的等命令逾時。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_artifact.py::test_save_step_output` | 參數化／測試資料準備 |
| `tests/test_executor.py::test_subprocess_executor_passes_timeout_to_subprocess` | monkeypatch、Mock |

<a id="v1-3-5"></a>

## v1.3.5

依據 Git tag `v1.3.5`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.3.5.md)。

本版 executor 測試替換 `subprocess.Popen`，用假 process 與串流模擬命令結果。這能檢查 executor 如何使用 subprocess，但不能證明 OS 真的建立或停止了程序。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_artifact.py::test_save_log_writer_step_stdout_and_stderr` | 參數化／測試資料準備 |
| `tests/test_executor.py::test_subprocess_executor_passes_timeout_to_subprocess` | monkeypatch、Mock |
| `tests/test_console_output.py::test_writer_displays_stdout_on_console` | tmp_path、capsys、parametrize |

<a id="v1-4-0"></a>

## v1.4.0

依據 Git tag `v1.4.0`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.4.0.md)。

本版 executor 測試替換 `subprocess.Popen`，用假 process 與串流模擬命令結果。這能檢查 executor 如何使用 subprocess，但不能證明 OS 真的建立或停止了程序。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_artifact.py::test_save_log_writer_step_stdout_and_stderr` | 參數化／測試資料準備 |
| `tests/test_executor.py::test_subprocess_executor_passes_timeout_to_subprocess` | monkeypatch、Mock |
| `tests/test_console_output.py::test_writer_displays_stdout_on_console` | tmp_path、capsys、parametrize |

<a id="v1-4-1"></a>

## v1.4.1

依據 Git tag `v1.4.1`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.4.1.md)。

本版 executor 測試替換 `subprocess.Popen`，用假 process 與串流模擬命令結果。這能檢查 executor 如何使用 subprocess，但不能證明 OS 真的建立或停止了程序。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_artifact.py::test_save_log_writer_step_stdout_and_stderr` | 參數化／測試資料準備 |
| `tests/test_executor.py::test_subprocess_executor_passes_timeout_to_subprocess` | monkeypatch、Mock |
| `tests/test_console_output.py::test_writer_displays_stdout_on_console` | tmp_path、capsys、parametrize |

<a id="v1-5-0"></a>

## v1.5.0

依據 Git tag `v1.5.0`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.5.0.md)。

本版 executor 測試替換 `subprocess.Popen`，用假 process 與串流模擬命令結果。這能檢查 executor 如何使用 subprocess，但不能證明 OS 真的建立或停止了程序。

測試把 `runner.runner.time.sleep` 換成 `fake_sleep(seconds)`，假函式只把秒數放進 list。最後檢查 `sleep_calls == [2]`，證明 runner 要求等待兩秒，而不需要真的暫停兩秒。這是該版本的單次 sleep 實作；後續 polling 版本的斷言不同。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_artifact.py::test_save_log_writer_step_stdout_and_stderr` | 參數化／測試資料準備 |
| `tests/test_executor.py::test_subprocess_executor_passes_timeout_to_subprocess` | monkeypatch、Mock |
| `tests/test_console_output.py::test_writer_displays_stdout_on_console` | tmp_path、capsys、parametrize |
| `tests/test_config_loader.py::test_retry_max_attempts_must_be_positive` | pytest.raises |
| `tests/test_runner.py::test_retry_waits_between_attempts` | monkeypatch 替換 sleep |

自訂 marker：`test_lifecycle`, `artifact`, `retry`。

<a id="v1-5-1"></a>

## v1.5.1

依據 Git tag `v1.5.1`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.5.1.md)。

本版 executor 測試替換 `subprocess.Popen`，用假 process 與串流模擬命令結果。這能檢查 executor 如何使用 subprocess，但不能證明 OS 真的建立或停止了程序。

測試把 `runner.runner.time.sleep` 換成 `fake_sleep(seconds)`，假函式只把秒數放進 list。最後檢查 `sleep_calls == [2]`，證明 runner 要求等待兩秒，而不需要真的暫停兩秒。這是該版本的單次 sleep 實作；後續 polling 版本的斷言不同。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_integration/test_integration.py::test_yaml_to_result_json` | tmp_path |
| `tests/test_unit/test_executor.py::test_subprocess_executor_passes_timeout_to_subprocess` | monkeypatch、Mock |
| `tests/test_unit/test_console_output.py::test_writer_displays_stdout_on_console` | tmp_path、capsys、parametrize |
| `tests/test_unit/test_artifact.py::test_save_log_writer_step_stdout_and_stderr` | 參數化／測試資料準備 |
| `tests/test_unit/test_config_loader.py::test_retry_max_attempts_must_be_positive` | pytest.raises |
| `tests/test_unit/test_runner.py::test_retry_waits_between_attempts` | monkeypatch 替換 sleep |

自訂 marker：`test_lifecycle`, `artifact`, `retry`。

<a id="v1-5-2"></a>

## v1.5.2

依據 Git tag `v1.5.2`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.5.2.md)。

本版 executor 測試替換 `subprocess.Popen`，用假 process 與串流模擬命令結果。這能檢查 executor 如何使用 subprocess，但不能證明 OS 真的建立或停止了程序。

測試把 `runner.runner.time.sleep` 換成 `fake_sleep(seconds)`，假函式只把秒數放進 list。最後檢查 `sleep_calls == [2]`，證明 runner 要求等待兩秒，而不需要真的暫停兩秒。這是該版本的單次 sleep 實作；後續 polling 版本的斷言不同。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_integration/test_integration.py::test_yaml_to_result_json` | tmp_path |
| `tests/test_unit/test_executor.py::test_subprocess_executor_passes_timeout_to_subprocess` | monkeypatch、Mock |
| `tests/test_unit/test_console_output.py::test_writer_displays_stdout_on_console` | tmp_path、capsys、parametrize |
| `tests/test_unit/test_artifact.py::test_save_log_writer_step_stdout_and_stderr` | 參數化／測試資料準備 |
| `tests/test_unit/test_config_loader.py::test_retry_max_attempts_must_be_positive` | pytest.raises |
| `tests/test_unit/test_runner.py::test_retry_waits_between_attempts` | monkeypatch 替換 sleep |

自訂 marker：`test_lifecycle`, `artifact`, `retry`。

<a id="v1-5-3"></a>

## v1.5.3

依據 Git tag `v1.5.3`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.5.3.md)。

本版 executor 測試替換 `subprocess.Popen`，用假 process 與串流模擬命令結果。這能檢查 executor 如何使用 subprocess，但不能證明 OS 真的建立或停止了程序。

測試把 `runner.runner.time.sleep` 換成 `fake_sleep(seconds)`，假函式只把秒數放進 list。最後檢查 `sleep_calls == [2]`，證明 runner 要求等待兩秒，而不需要真的暫停兩秒。這是該版本的單次 sleep 實作；後續 polling 版本的斷言不同。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_integration/test_integration.py::test_yaml_to_result_json` | tmp_path |
| `tests/test_unit/test_executor.py::test_subprocess_executor_passes_timeout_to_subprocess` | monkeypatch、Mock |
| `tests/test_unit/test_console_output.py::test_writer_displays_stdout_on_console` | tmp_path、capsys、parametrize |
| `tests/test_unit/test_artifact.py::test_save_log_writer_step_stdout_and_stderr` | 參數化／測試資料準備 |
| `tests/test_unit/test_config_loader.py::test_retry_max_attempts_must_be_positive` | pytest.raises |
| `tests/test_unit/test_runner.py::test_retry_waits_between_attempts` | monkeypatch 替換 sleep |

自訂 marker：`test_lifecycle`, `artifact`, `retry`。

<a id="v1-6-0"></a>

## v1.6.0

依據 Git tag `v1.6.0`；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.6.0.md)。

本版 executor 測試替換 `runner.executor.subprocess.Popen` 與 `time.perf_counter`，模擬程序仍在執行、時間已超過 deadline 的情境。測試不必真的等完整 timeout。

此版 delay 會反覆檢查時間與取消狀態，因此測試同時替換 `time.sleep` 與 `time.monotonic`。模擬的 sleep 只推進測試時間；模擬時鐘回報推進後的值，不必真的等待。只替換 sleep 卻不推進時鐘，可能讓等待迴圈無法按預期結束。

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_integration/test_integration.py::test_yaml_to_result_json` | tmp_path |
| `tests/test_unit/test_executor.py::test_subprocess_executor_polls_completed_subprocess` | monkeypatch、Mock |
| `tests/test_unit/test_console_output.py::test_writer_displays_stdout_on_console` | tmp_path、capsys、parametrize |
| `tests/test_unit/test_artifact.py::test_save_log_writer_step_stdout_and_stderr` | 參數化／測試資料準備 |
| `tests/test_unit/test_cancellation.py::test_raise_if_cancelled_raises_after_cancel` | pytest.raises |
| `tests/test_unit/test_runner.py::test_retry_waits_between_attempts` | 模擬時鐘與 `pytest.approx` |

自訂 marker：`cancelled`, `test_lifecycle`, `artifact`, `retry`。

<a id="v1-6-1"></a>

## v1.6.1

依據 v1.6.1 工作版本；覆蓋範圍見 [Test matrix](test_matrix/test_matrix_v1.6.1.md)。

本版 executor 測試替換 `runner.executor.subprocess.Popen` 與 `time.perf_counter`，模擬程序仍在執行、時間已超過 deadline 的情境。測試不必真的等完整 timeout。

`test_second_sigint_raises_keyboard_interrupt` 使用 `pytest.raises(KeyboardInterrupt)` 驗證第二次 SIGINT handler 呼叫。這是直接呼叫函式，沒有真的向 pytest 發送 Ctrl+C。

此版 delay 會反覆檢查時間與取消狀態，因此測試同時替換 `time.sleep` 與 `time.monotonic`。模擬的 sleep 只推進測試時間；模擬時鐘回報推進後的值，不必真的等待。只替換 sleep 卻不推進時鐘，可能讓等待迴圈無法按預期結束。

`test_executor_cleans_entire_tree_and_drains_readers` 的四列參數是 timeout/cancel × default/ignore。它使用 monkeypatch 包住真正的 `Popen` 與 reader join，先記錄物件，再呼叫原函式；因此仍會啟動真實程序。相對地，`test_group_probe_permission_error_does_not_abort_cleanup` 替換 OS 呼叫並使用 FakeProcess，完全模擬群組探測。**有使用 monkeypatch，不代表整個測試都是假的。**

| 實際案例 | 使用方式 |
| --- | --- |
| `tests/test_integration/test_integration.py::test_yaml_to_result_json` | tmp_path |
| `tests/test_integration/test_integration_cancellation.py::test_executor_cleans_entire_tree_and_drains_readers` | tmp_path、monkeypatch、四列參數化資料 |
| `tests/test_unit/test_console_output.py::test_writer_displays_stdout_on_console` | tmp_path、capsys、parametrize |
| `tests/test_unit/test_cancellation.py::test_raise_if_cancelled_raises_after_cancel` | pytest.raises |
| `tests/test_unit/test_runner.py::test_retry_waits_between_attempts` | 模擬時鐘與 `pytest.approx` |

自訂 marker：`cancelled`, `test_lifecycle`, `artifact`, `retry`。

<a id="v1-6-2"></a>

## v1.6.2 — Run-level Timeout

基準為 `eea8507` 加工作目錄修正，對照 v1.6.1 tag。本節不重述舊版測試結果。

- `test_config_loader.py` 使用 tmp_path 寫入省略 timeout 的 YAML，走完整 loader；參數化 NaN、±Infinity、零、負數與 bool 則直接測試 timeout parser。parser 測試不能證明所有 YAML 型別轉換。
- `test_run_timeout.py` 使用真實 thread、短 deadline 與最長兩秒輪詢，在 finally stop watchdog；不斷言精確排程時間。Stop 測試確認 join 完成與 token 未取消，未另等原期限。
- `test_run_status.py` 以 tuple 參數列驗證狀態優先順序；set 無序，不適合表示 reason／expected 的配對。
- `test_run_timeout_between_steps_stops_next_step` 使用專案自訂 fake executor 注入 RUN_TIMEOUT。它驗證 stage routing，不證明真實多步累計時間。
- `long_running.py` 與 `orphan_process.py` 是 subprocess 輔助腳本，不是 pytest fixtures。Fixture 路徑從巢狀測試檔的 `parents[2]` 找到專案根目錄。
- Runner integration tests 讀取 `result.json`，比對取消原因、狀態、attempt 數量與 flags；retry delay 情境保留 PROCESS_ERROR。這比僅檢查記憶體結果多驗證了序列化邊界，但仍未涵蓋 CLI exit code。
- Orphan test 先等待 direct child 結束，確認 descendant 仍活著，再呼叫 terminator；finally 防禦性清理測試程序。這只驗證同一 process group。

<a id="v1-6-2-command-quoting"></a>

### 組合 shell 命令：shlex.quote 與 repr

`test_integration_runner_timeout.py` 的 cleanup command 會經過兩層解析：先由 POSIX shell 拆解命令，再由 `python -c` 執行 Python 程式碼。因此，shell 參數與 Python 字串常值需要分別處理。

| 寫法 | 輸出用途 | 本次測試中的位置 |
| --- | --- | --- |
| `str(path)` | 將 Path 轉為路徑文字；不加引號或跳脫 | 傳給 quote 或 repr 前 |
| `shlex.quote(text)` | 將文字表示成一個 POSIX shell 參數 | Python executable、fixture 路徑、完整 `-c` 程式碼 |
| `repr(text)` | 將字串表示成可放入 Python 原始碼的字串常值，含引號與必要跳脫 | `Path(...)` 的參數 |

這些是 Python 標準函式庫／內建函式，不是 pytest 工具。`sys.executable` 指向目前執行測試的 Python，可讓 subprocess 使用同一個虛擬環境。

#### 1. shlex.quote：保留一個 shell 參數

```python
import shlex

fixture_path = "/tmp/test project/long_running.py"
quoted = shlex.quote(fixture_path)

assert quoted == "'/tmp/test project/long_running.py'"
assert shlex.split(quoted) == [fixture_path]
```

路徑包含空白時，直接拼接會被 shell 拆成多個參數。`quote()` 讓它保留為一個參數，也處理單引號、`$` 等 shell 特殊字元。它不一定每次都加引號：沒有特殊字元的字串可能原樣返回。

測試中的用法是分別引用每個參數，再組成命令：

```python
python = shlex.quote(sys.executable)
fixture = shlex.quote(str(fixture_script))
command = f"{python} {fixture}"
```

此片段接續測試中的 import 與 `fixture_script` 定義。不要對整條 `python fixture.py` 命令只呼叫一次 quote，否則 shell 會將整條文字視為單一參數。

#### 2. repr：產生 Python 字串常值

```python
import ast

path_text = "/tmp/test project/Andrew's cleanup.txt"
marker_path = repr(path_text)

assert ast.literal_eval(marker_path) == path_text
```

`repr()` 在這裡接收的是字串，因此結果可以嵌入 Python 程式碼。例如 `f"Path({marker_path})"` 會產生帶有正確引號的 `Path(...)` 呼叫。直接用 `str(marker)` 插入會缺少字串引號；手動包單引號又可能被路徑中的單引號截斷。

`repr()` 不是 shell quoting，不能代替 `shlex.quote()`。一般物件的 repr 也不保證是可執行的 Python 表達式；此技巧限定於本例的 `repr(str(marker))`。`f"{str(marker)!r}"` 是同樣的字串 repr 寫法。

#### 3. 組合兩層引用：完整可執行範例

以下示範與 cleanup 測試相同的組法，使用含空白與單引號的暫存路徑。範例會建立 marker、檢查內容，離開區塊後移除暫存目錄；它是教學範例，不是新增的 pytest 案例。

```python
import shlex
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory(prefix="runner example ") as directory:
    marker = Path(directory) / "Andrew's cleanup.txt"

    python = shlex.quote(sys.executable)
    marker_path = repr(str(marker))

    code = (
        "from pathlib import Path; "
        f"Path({marker_path}).write_text("
        "'cleanup completed', encoding='utf-8')"
    )
    cleanup_command = f"{python} -c " + shlex.quote(code)

    subprocess.run(cleanup_command, shell=True, check=True)

    assert marker.read_text(encoding="utf-8") == "cleanup completed"
```

處理順序是：`repr(str(marker))` 先保護 Python 程式碼中的路徑常值，再用 `shlex.quote(code)` 將完整程式碼保留成 `-c` 的單一參數。Shell 移除外層引用後，Python 才解析內層字串常值。

本專案 executor 使用 `shell=True`，因此需要 shell quoting。若直接使用 subprocess 的參數清單且不經 shell，則可寫成 `subprocess.run([sys.executable, "-c", code], check=True)`，不要再對清單元素呼叫 `shlex.quote()`；`code` 內嵌路徑仍需要 repr。`shlex.quote()` 適用於 POSIX shell，不應視為 Windows cmd.exe 或 PowerShell 的 quoting 方法。

現有 integration tests 驗證 cleanup marker 與報告結果，沒有專門參數化所有特殊字元路徑；本節範例也不代表該覆蓋已加入測試矩陣。

### 執行與定位案例

以下是可重跑的命令，實際觀察結果另見 [完成條件](definition_of_done/definition_of_done_v1.6.2.md)。

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/test_unit/test_run_timeout.py tests/test_unit/test_run_status.py -q
.venv/bin/python -m pytest tests/test_integration/test_integration_runner_timeout.py -q
```

AI 協作新增與修正案例、原始缺口及驗證限制集中於 [v1.6.2 matrix](test_matrix/test_matrix_v1.6.2.md)。本次文件補充以 AST 移除 docstring 後比較，確認可執行測試行為不變。
