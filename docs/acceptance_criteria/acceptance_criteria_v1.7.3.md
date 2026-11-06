# Device Test Runner v1.7.3 Acceptance Criteria

Scope: Configuration Validation. Verification uses the current working tree, not a published release.

| Criterion | Expected behavior | Evidence |
| --- | --- | --- |
| Structural validation | Unknown keys, invalid mappings/lists/scalars and numeric ranges fail before returning config | Schema parameterizations and source inspection |
| Error aggregation | ConfigurationValidationError is a ValueError with errors list and field diagnostics; first failing phase stops loading | Aggregation test, loader and validator inspection |
| Semantic validation | Duplicate names, unsupported types, invalid after_step and artifact constraints fail | Cross-field tests; untested branches listed in matrix |
| Minimal lifecycle | Omitted stages become empty steps; supplied stages require steps | Valid schema/loader test and source |
| Template compatibility | Schema accepts whole timeout templates without resolving env; runner later validates resolved values | Loader template assertion and existing resolver regressions |
| Python API boundary | Dataclass/run bypass loader checks; explicit semantic validator is available | Source inspection |
| Regression and version | Existing suites pass; package/runtime/report identify 1.7.3 | Completion record |
| Documentation | Current manual, README, guide, architecture UML and version records match implementation | Documentation audit |

Local test results and remaining checks are in the [completion record](../definition_of_done/definition_of_done_v1.7.3.md). Test coverage limitations are in the [matrix](../test_matrix/test_matrix_v1.7.3.md). Hardware/demo validation and release acceptance remain open.
