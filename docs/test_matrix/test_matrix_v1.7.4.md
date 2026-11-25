# Device Test Runner v1.7.4 Test Matrix

Scope: Execution Manifest. Reviewed source 0b72805, draft f6b05dd, tests 4b7fea4 and existing working-tree corrections. See [pytest techniques](../test_guide.md#v1-7-4) and [execution record](../definition_of_done/definition_of_done_v1.7.4.md).

## Requirement coverage

All seven functions are in tests/test_unit/test_execution_manifest.py; they collect seven cases. Despite its directory, the first two run real local subprocesses without device hardware.

| Requirement | Test function | Direct assertion |
| --- | --- | --- |
| YAML-to-manifest flow | test_manifest_ene_to_end | Schema 1, runner 1.7.4, COMPLETED, result status/time equality, numeric resolved timeout, absolute rule path, 64-character hash, result.json exists |
| Referenced environment masking | test_manifest_masks_referenced_environment | One referenced serial absent from manifest text; expected marker present |
| Stable hashes | test_hash_is_stable_for_same_config | Same input gives equal source and resolved hashes |
| Configuration changes | test_hash_changes_when_repeat_changes | Changed repeat changes source hash |
| Atomic overwrite | test_atomic_save_replaces_existing | Second save is readable as COMPLETED; no temporary files remain after success |
| Dataclass contract | test_manifest_fails_on_non_dataclass | Dictionary input raises TypeError |
| Exact canonical digest | test_manifest_hashes_canonical_utf8_config | Unicode and Path input matches an independent SHA-256 of expected compact sorted UTF-8 JSON |

## Corrections and collaboration

Existing local source corrections retain original_config, move hexdigest to the hash object and finalize the manifest after reporting. The draft previously called hexdigest on bytes and could not complete hashing. The independent canonical digest case guards the corrected bytes-to-hash behavior. The end-to-end case checks final state and report metadata, but does not directly guard original-config preservation.

Existing local test corrections replace an invalid assignment assertion with path equality, use the correct redaction marker, explicitly reference DEVICE_SERIAL in the fixture and provide real CSV generation. These restore intended assertions; the fixture previously supplied an environment value without referencing it. This documentation task adds seven Given/When/Then docstrings only; executable test AST is preserved. No original authorship is inferred and no new behavioral test is attributed to this task.

## Inspected behavior and gaps

PREPARED ordering before the first process, reporter/write exceptions, fsync/replace failures, crash recovery, normal cancellation/timeout completion, multiple referenced values and directory-dependent hashes are inspected contracts without dedicated manifest assertions. Success-path overwrite is not evidence of atomicity under crashes. Single-value masking is not evidence of complete secret protection: the source returns after its first candidate. No external Android tools, hardware, Windows or remote release is validated.
