# Device Test Runner v1.7.4 Acceptance Criteria

Scope: Execution Manifest in the current working tree; release publication unverified.

| Criterion | Expected behavior | Evidence |
| --- | --- | --- |
| Preparation | Save schema-1 PREPARED manifest after resolution, before subprocesses | Source order inspection; final output exercised by end-to-end test |
| Configuration snapshot | Persist configuration with resolved device, lifecycle and artifact.validation | End-to-end timeout/path assertions and source inspection |
| Fingerprints | SHA-256 of redacted canonical UTF-8 JSON; not raw YAML | Stability, mutation and independent canonical digest tests |
| Completion | After reporter save, add COMPLETED, result_status and finished_at | End-to-end metadata assertions and source inspection |
| Storage | Same-directory temporary file, fsync and replace; remove leftover temp on normal save | Source inspection and successful overwrite test; failure injection pending |
| Input contract | Reject non-dataclass configs | TypeError test |
| Masking boundary | Single referenced env value is masked; multiple candidates are limited by early return | Single-value test and source inspection; full secrecy is not accepted |
| Compatibility | Existing result schema retained; version 1.7.4 | Reporter/runtime/package inspection and regression suite |
| Documentation | Current manual, guide, UML and version records describe actual behavior | Local documentation audit |

Local results and open release checks are in the [completion record](../definition_of_done/definition_of_done_v1.7.4.md). Acceptance is limited to the behavior and evidence above. Failure-path and multi-environment coverage remain open in the [matrix](../test_matrix/test_matrix_v1.7.4.md).
