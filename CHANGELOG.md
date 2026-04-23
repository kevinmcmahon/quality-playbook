# Changelog

All notable changes to the Quality Playbook will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.1] — 2026-04-22

### Fixed

- **Phase 5 writeup stub regression.** `bin/run_playbook.py::phase5_prompt` now carries a MANDATORY HYDRATION STEP with a BUGS.md → writeup field map, a worked BUG-004 example, and a per-writeup confirmation checklist that prohibits empty backticks, empty diff fences, and angle-bracket placeholders. This closes the Phase 5 failure mode observed on `bus-tracker-1.5.0`, where the playbook produced skeletal writeups that passed the legacy gate.

### Added

- **Quality-gate writeup hydration checks.** `check_writeups` now fails when any writeup contains one of five template-sentinel strings (``"is a confirmed code bug in ``"``, ``"The affected implementation lives at ``"``, ``"Patch path: ``"``, ``"- Regression test: ``"``, ``"- Regression patch: ``"``) or when a ` ```diff ` fence is present but contains no `+` / `-` lines other than file headers.

### Changed

- **Case-insensitive diff fence detection.** Quality gate recognises ` ```diff `, ` ```Diff `, and ` ```DIFF ` uniformly, so inline-diff presence and content checks can't disagree on whether a fence exists. Previously a writeup with a mixed-case fence would trip a confusing "no inline fix diffs" FAIL despite containing a visible unified diff.

## [1.5.0] — baseline

Initial release under Semantic Versioning. Features include the formal-docs pipeline (plaintext + `.meta.json` sidecars), the phase orchestrator, the quality gate with §10 mechanical checks, the Council-of-Three semantic citation check, the tier taxonomy, and the challenge-gate iteration-coverage invariant. Pre-1.5.0 history lives in `docs_gathered/01_README_project.md` under "What's new in v1.4.x".
