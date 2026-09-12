# Device Test Runner v1.6.0 Definition of Done

Release theme: Cancellation Foundation

## Product and Architecture

- [x] CancellationToken exposes active/cancelled state, idempotent cancellation and exception helper.
- [x] Runner accepts an optional token and stops normal work on observed cancellation.
- [x] Executor distinguishes cancellation from timeout and preserves captured output.
- [x] Cancellation is non-retryable; retry delay checks the token in polling intervals.
- [x] Reachable cleanup uses a fresh token and final artifact validation still runs.
- [x] Report exposes cancellation flags, request metadata, counts and CANCELLED status.
- [x] Runtime metadata identifies `1.6.0`.
- [x] Process-tree, signal, exception and timing limitations are explicit in Architecture.

## Quality

- [x] Token, retry policy, configuration rejection and lifecycle routing have unit coverage.
- [x] Real subprocess tests distinguish cancellation from timeout and check captured stdout.
- [x] Report serialization and final artifact cancellation precedence are covered.
- [x] All 150 test functions have meaningful Given／When／Then descriptions.
- [x] AST comparison confirms test behavior unchanged by docstring edits.

Verification on 2026-09-12 (local Python 3.14): `.venv/bin/python -m pytest -q` → **153 passed in 39.39s**. This is local evidence, not a successful GitHub Actions Python 3.12 run. `git diff --check` passed; local Markdown links and JSON examples validated.

### Sample Configuration

2026-09-12 本機載入 `configs/sample.yaml`，只將 `artifact.output_dir` 改為暫存目錄後，使用真實 runner/executor 執行。觀察到：`status=FAILED`、configured 9、executed 8、passed 7、failed 1、cancelled 0、skipped 1；8 個 artifact rules 中 3 passed、5 required failures。`run_unstable_command` 第一個 attempt 為 process error，sample 的 retry_on 未包含此類型，所以沒有重試，下一步 `run_retry_command` 被跳過。報告成功寫出，但不是全數通過的 sample。

未在這個文件任務修改 sample 或 scripts。`scripts/unstable.sh` 檢查的是 literal `COUNTER_FILE`，`scripts/artifact_retry.sh` 的 mkdir 未正確展開 `$RUN_ARTIFACT_DIR`；這些 source findings 也需在獨立修正中處理。

## Documentation and Release

- [x] README and four v1.6.0 documents reflect source behavior and compatibility changes.
- [x] Roadmap records implemented cancellation foundation and remaining guarantees.
- [x] CHANGELOG records v1.6.0 implementation, packaging and workflow changes.
- [x] Older versioned documents are preserved as history.
- [x] Package/distribution version is synchronized to `1.6.0` in `pyproject.toml`.
- [ ] Sample configuration completes with PASSED.
- [ ] Related GitHub issue closure is verified.
- [ ] Git tag `v1.6.0` is created (absent from inspected local tag refs).
- [ ] GitHub Release notes are verified as published.

Release readiness: cancellation foundation is implemented and locally tested. A passing sample configuration, issue closure verification, release tagging and publication remain pending.
