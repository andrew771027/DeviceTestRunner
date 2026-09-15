# Device Test Runner v1.4.1 Acceptance Criteria

## Scope

CSV and JSON validation.

Version baseline: Git tag `v1.4.1`

This document preserves the recorded acceptance state for this version. Test results and release checks below are historical records; they have not been rerun or reverified by this formatting update.

## Acceptance criteria

| ID | Given | When | Then |
| --- | --- | --- | --- |
| AC-1 | CSV column and row requirements | The validator checks the file | CSV validation checks required columns and minimum data rows. |
| AC-2 | A missing, unreadable, malformed or non-file CSV target | CSV validation runs | CSV validation safely reports missing, unreadable, malformed, or non-file targets. |
| AC-3 | Required nested JSON paths | The validator checks the document | JSON validation checks required nested paths. |
| AC-4 | Expected JSON values | The validator compares actual and expected values | JSON expected values preserve type-sensitive comparison. |
| AC-5 | Content-validation options in YAML | The loader reads the configuration | Content-validation options load correctly from YAML. |
| AC-6 | Invalid CSV or JSON content | The runner validates artifacts and builds the report | Invalid CSV or JSON content affects final run status and report output. |
| AC-7 | Existing v1.4.0 validation rules | The updated validator evaluates them | v1.4.0 validation rules remain compatible. |

## Verification

- [x] AC-1 through AC-7 are marked complete in the recorded baseline.

Related records: [Test matrix](../test_matrix/test_matrix_v1.4.1.md) · [Definition of done](../definition_of_done/definition_of_done_v1.4.1.md).

## Acceptance decision

Accepted at Git tag `v1.4.1`, as recorded in the original acceptance checklist.
