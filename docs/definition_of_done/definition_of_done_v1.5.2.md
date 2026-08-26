# Device Test Runner v1.5.2 Definition of Done

Release theme: Failure Classification

## Product and Architecture

- [x] `FailureType` 定義 success、process 與 artifact failure categories。
- [x] `FailureClassifier` 將 timeout、device-offline patterns、一般 process error 與 artifact failure 分類。
- [x] Process failure 優先於 artifact failure，artifact missing 優先於 artifact invalid。
- [x] `RetryPolicy` 使用 failure type 與 attempt limit 決定 retry。
- [x] `StepAttemptResult` 與 JSON report 保存 failure type 和原始診斷資料。
- [x] Runner metadata version 為 `1.5.2`。

## Quality

- [x] Unit tests 覆蓋 classifier、executor、validator、retry policy、runner 與 reporter。
- [x] Integration tests 覆蓋 timeout、device offline 與一般 process error。
- [x] Artifact-aware retry integration test 通過。
- [x] 所有 test cases 具有 Given／When／Then acceptance description。
- [x] 完整 pytest suite 通過：112 passed。

## Documentation and Release

- [x] README 更新 v1.5.2 current capability、report schema 與文件連結。
- [x] Architecture、Test Matrix 與 Acceptance Criteria 已建立。
- [x] CHANGELOG 記錄 v1.5.2。
- [x] Roadmap 加入 v1.5.2 release milestone。
- [ ] `v1.5.2` Git tag 建立。
- [ ] GitHub release notes 發布。

Release readiness: implementation、tests 與 repository documentation 已完成；tag 與 GitHub Release 仍待 release owner 執行。
