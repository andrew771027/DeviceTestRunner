# Device Test Runner v1.7.0 Definition of Done

Version scope: Static Variable Substitution. Source baseline: `194faf3` plus the inspected working tree. Package version is already declared as 1.7.0; runtime and report assertions are synchronized during this update. This is a local completion record, not release publication evidence.

## Implementation and documentation

- [x] Optional variables mapping is validated at load time; command, step timeout and validation path templates are retained until the run directory exists.
- [x] vars.NAME and absolute run.dir resolve before normal watchdogs and subprocesses start.
- [x] Whole references preserve types; embedded values render strings. Step timeouts accept finite positive int/float and reject bool and numeric strings.
- [x] Resolution uses immutable configuration copies; separate runs resolve their own directories.
- [x] Runtime, package declaration and report expectations use 1.7.0.
- [x] README, user manual, static-variable guide, changelog, roadmap and testing guide match current supported fields and limits.
- [x] v1.7.0 architecture contains classDiagram and sequenceDiagram aligned with source, including pre-execution error branches.
- [x] Test matrix and acceptance criteria distinguish direct assertions, source inspection and missing evidence.
- [x] variables.py documents phase separation, namespaces, type checks, exceptions, allowlisted dataclasses and immutable replacement.
- [x] All 212 test functions have concrete Given/When/Then descriptions; 16 static-variable descriptions added without changing their executable AST.
- [x] Historical version documents and previous results retained.

## Local verification — 2026-10-14

Environment: macOS 26.7.1 x86_64, repository `.venv` Python 3.14.8. Results below were observed in this update; they are not Linux CI evidence.

| Check | Actual command / method | Observed result |
| --- | --- | --- |
| Baseline before edits | `.venv/bin/python -m pytest -q` | 260 passed in 48.21s |
| After runtime/version assertions and descriptions | `.venv/bin/python -m pytest -q` | 260 passed in 48.39s |
| Static variable tests | `.venv/bin/python -m pytest -q tests/test_unit/test_variables.py tests/test_integration/test_integration_static_variables.py` | 37 passed in 0.80s |
| Package configuration and lock | `poetry check --lock` | All set! |
| Package version | `poetry version --short` | 1.7.0 |
| Runtime/report | Real run of advance_sample via Python API; inspect result.json | metadata.runner_version is 1.7.0 |
| Provided YAML | ConfigLoader.load for basic_sample.yaml and advance_sample.yaml | Both loaded; basic sample not executed |
| Static-variable example | Execute advance_sample through actual SubprocessExecutor with ArtifactManager output redirected to a temporary directory | PASSED; power_result.csv has header plus two rows; report version 1.7.0 |
| Documentation examples | Load complete YAML in README, user manual and static-variable guide; execute device-free examples through actual runner | README quick start, first manual example and static-variable example PASSED; device-oriented manual example loaded only |
| Python / JSON examples | ast.parse Python fences and json.loads JSON fences in the inspected usage documents | Passed |
| Descriptions | AST audit of all tests for Given/When/Then; compare both static-variable test files without docstrings against staged baseline | 212 functions; no missing descriptions; executable AST unchanged |
| Documentation links and references | Local Markdown link/fence audit and AST test-name checks | 88 local links and fully qualified matrix test references verified |
| Whitespace | `git diff --check` | Passed |
| Formatting tool availability | `.venv/bin/python -m black --check runner/variables.py tests/test_unit/test_variables.py tests/test_integration/test_integration_static_variables.py --line-length=100` | Not run: black is not installed in this virtual environment; no lint/format pass claimed |

YAML verification redirects output to temporary directories so the repository's sample artifact destination is not populated. Successful example runs establish local shell, resolver, validation and report behavior; they do not validate device tools or untrusted shell input.

Whitespace and local link checks passed after documentation editing. Runtime synchronization changes the declaration and four expected report versions; it does not install a new distribution.

## Release and follow-up

- [ ] Create or verify local v1.7.0 tag; no such tag was found in the inspected local tag list.
- [ ] Verify GitHub Release, issue/milestone state and Linux CI. These external states were not queried.
- [ ] Reinstall and verify the installed distribution version; package declaration/lock consistency alone is not installation evidence.
- [ ] Run configured lint/formatter checks in an environment with the tools available.
- [ ] Add dedicated assertions for variables null/omission, all cleanup stages, retry interactions, field exclusions and unsupported dataclasses.
- [ ] Add direct executor/watchdog call assertions for fail-fast errors and fractional timeout interruption through variable references.
- [ ] Address existing exception-safe finalization, CLI TIMED_OUT exit code, detached descendants and real CLI signal/platform verification.
- [ ] Design environment mappings and runtime context separately; recursive templates, literal escaping and arithmetic remain unsupported.

The implemented feature and local tests are verified. Unchecked release and coverage items remain open. This task does not create a commit, push, tag or GitHub Release.
