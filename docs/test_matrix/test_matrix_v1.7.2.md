# Device Test Runner v1.7.2 Test Matrix

Scope: Device Runtime Context. Source `940fe66`, tests `2aeb559`, guide draft `278e012`; inspected against local HEAD. See [pytest techniques](../test_guide.md#v1-7-2) and [execution record](../definition_of_done/definition_of_done_v1.7.2.md).

## Requirement coverage

| Requirement | Test path / function | Direct assertions and boundary |
| --- | --- | --- |
| Resolved device references and unchanged input | `tests/test_unit/test_runtime_context.py::test_device_context_in_command_and_artifact` | Env-backed serial and literal product appear in command; original command retains template. Artifact path checks run.dir/vars, not device namespace |
| Reject early lookup | Same file: `test_context_is_not_bound_early` | Unbound serial lookup raises VariableResolutionError |
| Reject unknown field | Same file: `test_unknown_device_field` | Bound device.imei lookup raises unsupported context error |
| Reject repeated binding | Same file: `test_context_cannot_be_rebound` | Second bind of same DeviceInfo raises already bound |
| Reject unresolved/empty metadata | Same file: `test_unresolved_device_metadata_is_rejected` | Three serial inputs: empty, device template, env template; no direct product/build/non-string cases |
| Snapshot stability | Same file: `test_device_metadata_from_env_is_snapshotted` | Host changes after construction; serial remains before through binding and lookup |
| YAML → real subprocess → CSV validation | `tests/test_integration/test_integration_static_variables.py::test_runtime_context_end_to_end` | Resolved serial metadata and command, PASSED, successful CSV validation, unchanged command template. JsonReporter runs but JSON is not read back; CSV cells are not asserted |
| Invalid command device key | Same integration file: `test_runtime_context_unknown_key_fails_before_subprocess` | Raises unsupported device context and no result.json; no execute spy or process marker |
| Regression | Full `poetry run pytest -q` | Static/env, lifecycle, retry, cleanup, cancellation, artifacts and reporting suites; not dedicated context coverage for every branch |
| Version alignment | Existing runner/integration report assertions plus package/runtime inspection | Expected runner version updated to 1.7.2 in test commit; no new report schema |

Six new unit functions collect eight cases due to serial parameterization; two integration functions add two cases. The suite grows from 271 to 281 collected cases. Current AST audit finds 229 test functions, each with Given/When/Then descriptions; function count differs from collected case count.

## Collaboration and corrections

The test commit adds coverage for device interpolation, binding errors and snapshot reuse. The documentation update adds meaningful Given/When/Then descriptions to those eight functions without changing executable AST. Git history does not establish AI authorship for the original cases, so no author attribution is inferred.

The draft guide claimed broader unit build coverage and JSON verification than the assertions provide. Current guide and matrix distinguish actual assertions from source inspection; no product fix was needed or claimed.

## Source-inspected behavior and gaps

bind_device validates all three fields, copies them and rejects unresolved templates before run directory allocation. Product/build remain literal, context values are strings, and whitespace-only strings pass. These details are inspected in source; dedicated tests do not cover every field/type combination.

Still missing: device.build interpolation, device namespace in validation path, product/build invalid values and non-string metadata, binding failure before allocation through runner, context timeout rejection, retry/multiple-run device snapshot behavior, direct proof of no subprocess on unknown field, and read-back of context JSON/CSV contents in the integration test. The device-free documentation example separately verifies output contents and JSON locally; it is not an added regression test.

No hardware, device discovery, remote execution, Windows behavior or release publication is established by these cases.
