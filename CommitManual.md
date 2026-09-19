# 提交與發佈檢查清單

提交前逐項確認。只修改文件時，在提交說明中註明不適用的程式或測試項目。

## 提交前

- [ ] 確認版本號；需要升版時，同步套件、runtime 與報告版本。
- [ ] 檢查程式變更是否符合需求，移除暫存程式與除錯輸出。
- [ ] 更新受影響的測試，執行相關測試並記錄結果。
- [ ] 檢查 `tests/` 下每個 Python 測試函式的 docstring，使用具體的 `Given`、`When`、`Then` 行說明前提、操作與預期結果。
- [ ] 更新 [README](README.md) 的使用方式、範例與限制。
- [ ] 更新對應版本的架構文件，確認介面與資料流。
- [ ] 在版本架構文件中加入或更新 Mermaid UML：使用 `classDiagram` 說明主要類別與關係，使用 `sequenceDiagram` 說明關鍵執行流程。圖中的名稱、呼叫順序與分支須符合該版本實作；規劃中的設計須另外標示。
- [ ] 在 [CHANGELOG](CHANGELOG.md) 記錄使用者可觀察的變更。
- [ ] 更新完成條件，區分已驗證與尚未完成的項目。
- [ ] 更新測試矩陣，讓需求能對應到測試。
- [ ] 更新 [測試指南](docs/test_guide.md) 的 pytest 用法大綱與對應版本案例；AI 新增或修改測試所使用的技巧也需納入。
- [ ] 更新驗收條件，寫出可確認的預期行為。
- [ ] 更新 [Roadmap](docs/roadmap.md)，同步已實作功能與後續規劃。
- [ ] 保留舊版文件的歷史內容；新版本依既有語言、標題、檔名與 Markdown 格式撰寫。
- [ ] 以程式、設定、測試、完整 Git 歷史與 diff 核對內容。舊文件與實作不同時，以實際程式和測試行為為準。
- [ ] 新增測試結果時，只記錄本次實際觀察到的命令、環境與結果；歷史紀錄保留原本的日期與基準。
- [ ] 檢查文件：先說用途，使用短句與具體動詞；保留必要術語，刪除空泛宣傳與重複結論。
- [ ] 執行 `git diff --check`，檢查連結、命令與範例。

## 發佈前

- [ ] 確認該版本的完成條件與驗收條件已滿足。
- [ ] 確認 tag 指向預定發佈的 commit，並與版本號一致。
- [ ] 確認 GitHub Release 已發布，內容與該版本的變更一致。

## 手動文件更新 workflow

[manual.yml](.github/workflows/manual.yml) 透過 `workflow_dispatch` 更新版本文件與測試說明。它會執行測試，並在有變更時直接 commit、push 到指定分支。升版、建立 tag 與發布 GitHub Release 需另外完成。

### 執行前

- [ ] `release_version` 使用不含 `v` 的 `MAJOR.MINOR.PATCH`，例如 `1.6.0`。
- [ ] `target_branch` 指向既有分支，且允許 workflow push；預設為 `main`。
- [ ] 確認 `model` 是 API 專案可使用的模型。
- [ ] 設定 repository secret `OPENAI_API_KEY`。Workflow 在執行 CLI 時將它傳入 `CODEX_API_KEY`。

Workflow 使用 Ubuntu、Python 3.12 與 Node.js 22，透過 `pip install .` 安裝專案，再安裝最新版 Codex CLI。Job 上限為 30 分鐘；相同目標分支共用 concurrency group，不會取消正在執行的 job。

### 更新範圍

Codex 必須先完整閱讀本清單，並核對下列文件。`<version>` 代表輸入的版本號。

| 文件 | 核對內容 |
| --- | --- |
| `README.md` | 使用方式、範例與限制 |
| `docs/architecture/architecture_v<version>.md` | 架構、介面、資料流，以及符合該版本實作的 UML 類別圖與循序圖 |
| `docs/test_matrix/test_matrix_v<version>.md` | 測試覆蓋、證據與 AI 協作新增或補強的案例，連結至測試指南的對應版本 |
| `docs/test_guide.md` | Pytest 用法大綱、工具分類、版本索引與各版實際案例 |
| `docs/acceptance_criteria/acceptance_criteria_v<version>.md` | 驗收條件與結論 |
| `docs/definition_of_done/definition_of_done_v<version>.md` | 完成狀態與待辦項目 |
| `docs/roadmap.md` | 版本進度與後續規劃 |
| `CHANGELOG.md` | 該版本的實際變更 |
| `tests/` 下的 Python 測試 | 有意義的 Given／When／Then docstring |

文件任務只在需要時修改測試說明，不應為了更新文件改變產品行為。功能、測試數量、結果、tag、release 與 issue 狀態都必須有證據。未確認的發佈項目保持未勾選；Git tag 的存在不能證明 GitHub Release 已發布。

### 測試指南與 test matrix 的分工

[測試指南](docs/test_guide.md) 集中說明測試怎麼寫、使用哪些 pytest 工具；各版 test matrix 說明測試涵蓋哪些需求、修正與限制。教學內容放在指南，矩陣連結至指南的對應版本，避免重複維護。

AI 更新測試文件時，需同步核對以下項目：

- 維護指南的用法大綱與版本索引，依實際使用情況整理函式、fixture、Mock／Fake、參數化與執行方式。
- 各版說明依對應 Git tag、commit 或明確工作版本撰寫，不將最新版用法套回舊版；保留歷史結果與日期。
- 共通用法集中說明，各版只記錄差異與實際測試案例，避免重複教學。
- 區分框架提供的工具、專案輔助程式與示意範例；未使用的功能不列為已實作，範例不算測試證據。
- 新增版本或測試技巧時更新指南；只為補充說明時，不改變產品與測試行為。

#### AI 協作案例與修正紀錄

- 將 AI 新增、補強或修正的案例納入矩陣，分別寫出測試名稱、原本缺口、主要斷言與仍未涵蓋的情境。有協作紀錄才標示來源，不憑程式風格推測作者。
- 重要修正需說明「原本為何失敗 → 修改了什麼 → 哪個測試防止再次發生」。區分產品程式的問題與測試資料、Mock 設定或路徑錯誤。
- 說明測試的驗證範圍與限制，具體做法記錄在對應版本的 test matrix。
- 保留既有程式風格，以容易閱讀的註解與範例解釋必要概念；不為了補文件改寫測試行為。

#### 文件檢查

- [ ] 測試路徑、函式名稱與 API 用法已對照該版本原始碼。
- [ ] 範例語法、Markdown code fence、連結與執行指令已檢查。
- [ ] 執行指令與實際執行結果分開記錄；未執行的測試不寫成通過。
- [ ] 已說明模擬與真實操作的邊界，沒有把單元測試擴大解讀成端到端保證。

### 驗證與提交

1. 修改前執行 `pytest -q`，確認基準測試通過。
2. Codex 完成編輯後，執行 `pytest -q` 與 `git diff --check`。
3. Workflow 再次執行上述檢查，並比較測試函式數量與 Given／When／Then 行數。
4. 有變更時，以 `github-actions[bot]` 提交，訊息為 `docs: update Device Test Runner v<version>`，再 push 到 `target_branch`。

目前行數檢查只計算以 `def test_` 開頭的函式，以及縮排四個空白、以 `Given `、`When `、`Then ` 開頭的行。三種描述的行數都必須等於測試函式數。這只檢查總數，仍需人工確認每個測試的描述有意義且符合實際斷言。

Codex 編輯步驟只留下工作目錄變更，不自行 commit、push 或修改 GitHub 設定；提交由後續 workflow 步驟負責。該步驟會暫存 `README.md`、`CHANGELOG.md`、`docs/` 與 `tests/` 下的所有變更，沒有變更時跳過提交。`CommitManual.md`、`site/`、workflow 與版本設定檔不在自動提交範圍內，修改後需另行提交。

此流程不建立 PR、tag 或 GitHub Release，也不會自動完成本清單中的套件／runtime 升版與發佈檢查。
