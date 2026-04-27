"""bin/skill_derivation/__main__.py — CLI entry point for the four-pass pipeline.

Usage:
    python3 -m bin.skill_derivation <target_dir> [options]

Options:
    --pass A|B|C|D|all          Pass to run; "all" runs A->B->C->D in
                                sequence with B4 upstream-status gate
                                enforced at each transition.
    --resume                    Resume from cursor (default behavior).
                                Pass --no-resume to start fresh.
    --runner claude|copilot     LLM runner for Pass A. Default:
                                claude (subprocess `claude --print
                                --model sonnet`).
    --pace-seconds N            Sleep N seconds between LLM calls in
                                Pass A. Used to throttle against rate
                                limits.
    --project-type-path PATH    Path to project_type.json. Default:
                                <target_dir>/quality/project_type.json.
                                Required by Pass C.
    --skill-md PATH             Path to SKILL.md. Default:
                                <target_dir>/SKILL.md.
    --references-dir PATH       Path to references/. Default:
                                <target_dir>/references.
    --pass-spec-path PATH       Path to the per-pass spec doc for the
                                recovery preamble. Default:
                                ~/Documents/AI-Driven Development/
                                Quality Playbook/Reviews/
                                QPB_v1.5.3_Phase3b_Brief.md
    --no-resume                 Start passes from scratch.

The orchestration enforces the B4 upstream-status gate: when --pass
all is used, Pass B refuses to start unless Pass A reached
status="complete"; Pass C refuses unless Pass B is complete; Pass D
refuses unless Pass C is complete. Refusal raises
protocol.UpstreamIncompleteError with a diagnostic naming the
downstream pass that refused.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from bin.skill_derivation import (
    pass_a,
    pass_b,
    pass_c,
    pass_d,
    protocol,
    sections,
)
from bin.skill_derivation.runners import make_runner


_DEFAULT_PASS_SPEC_PATH = Path(
    "/Users/andrewstellman/Documents/AI-Driven Development/"
    "Quality Playbook/Reviews/QPB_v1.5.3_Phase3b_Brief.md"
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python3 -m bin.skill_derivation",
        description=(
            "QPB v1.5.3 Phase 3 / 3b four-pass skill-derivation "
            "pipeline. Reads SKILL.md + reference files; produces "
            "draft REQs, mechanical citations, formal REQ records, "
            "and a coverage audit. See "
            "QPB_v1.5.3_Phase3b_Brief.md for the contract."
        ),
    )
    parser.add_argument("target_dir", type=Path)
    parser.add_argument(
        "--pass",
        dest="pass_choice",
        choices=("A", "B", "C", "D", "all"),
        default="all",
        help='Which pass to run. "all" runs A->B->C->D in sequence.',
    )
    parser.add_argument(
        "--no-resume",
        dest="resume",
        action="store_false",
        default=True,
        help="Start passes from scratch (default: resume from cursor).",
    )
    parser.add_argument(
        "--runner",
        choices=("claude", "copilot"),
        default="claude",
        help="LLM runner for Pass A (default: claude).",
    )
    parser.add_argument(
        "--pace-seconds",
        type=int,
        default=0,
        help="Sleep N seconds between Pass A LLM calls.",
    )
    parser.add_argument("--project-type-path", type=Path, default=None)
    parser.add_argument("--skill-md", type=Path, default=None)
    parser.add_argument("--references-dir", type=Path, default=None)
    parser.add_argument(
        "--pass-spec-path",
        type=Path,
        default=_DEFAULT_PASS_SPEC_PATH,
    )
    return parser.parse_args(argv)


def _phase3_dir(target_dir: Path) -> Path:
    return target_dir / "quality" / "phase3"


def _enumerate_for_pass_a(args: argparse.Namespace, target_dir: Path) -> Path:
    """Run section enumeration over SKILL.md + references/ and write
    pass_a_sections.json. Returns the path to the sections JSON.
    """
    skill_md = args.skill_md or (target_dir / "SKILL.md")
    refs = (
        args.references_dir
        if args.references_dir is not None
        else target_dir / "references"
    )
    secs = sections.enumerate_skill_and_references(
        skill_md, refs if refs.is_dir() else None, target_dir
    )
    out = _phase3_dir(target_dir) / "pass_a_sections.json"
    sections.write_sections_json(secs, out)
    return out


class _PacingRunner:
    """Wraps an LLMRunner with a sleep between calls."""

    def __init__(self, inner, pace_seconds: int) -> None:
        self._inner = inner
        self._pace = pace_seconds
        self._call_count = 0

    def run(self, prompt: str):
        if self._call_count > 0 and self._pace > 0:
            time.sleep(self._pace)
        self._call_count += 1
        return self._inner.run(prompt)


def _run_pass_a(args: argparse.Namespace, target_dir: Path) -> int:
    sections_path = _enumerate_for_pass_a(args, target_dir)
    p3 = _phase3_dir(target_dir)
    refs_dir = (
        args.references_dir
        if args.references_dir is not None
        else target_dir / "references"
    )
    config = pass_a.PassAConfig(
        drafts_path=p3 / "pass_a_drafts.jsonl",
        progress_path=p3 / "pass_a_progress.json",
        sections_path=sections_path,
        pass_spec_path=args.pass_spec_path,
        document_root=target_dir,
        uc_drafts_path=p3 / "pass_a_use_case_drafts.jsonl",
        req_template_path=Path(__file__).parent / "prompts" / "pass_a_section.md",
        uc_template_path=Path(__file__).parent / "prompts" / "pass_a_uc_section.md",
        references_dir=refs_dir if refs_dir.is_dir() else None,
    )
    inner_runner = make_runner(args.runner)
    runner = (
        _PacingRunner(inner_runner, args.pace_seconds)
        if args.pace_seconds > 0
        else inner_runner
    )
    return pass_a.run_pass_a(
        config,
        runner,
        config.req_template_path,
        resume=args.resume,
    )


def _run_pass_b(args: argparse.Namespace, target_dir: Path) -> int:
    p3 = _phase3_dir(target_dir)
    refs_dir = (
        args.references_dir
        if args.references_dir is not None
        else target_dir / "references"
    )
    skill_md = args.skill_md or (target_dir / "SKILL.md")
    config = pass_b.PassBConfig(
        drafts_path=p3 / "pass_a_drafts.jsonl",
        citations_path=p3 / "pass_b_citations.jsonl",
        progress_path=p3 / "pass_b_progress.json",
        skill_md_path=skill_md,
        references_dir=refs_dir if refs_dir.is_dir() else None,
        document_root=target_dir,
        pass_a_progress_path=p3 / "pass_a_progress.json",
    )
    return pass_b.run_pass_b(config, resume=args.resume)


def _run_pass_c(args: argparse.Namespace, target_dir: Path) -> int:
    p3 = _phase3_dir(target_dir)
    project_type_path = (
        args.project_type_path
        if args.project_type_path is not None
        else target_dir / "quality" / "project_type.json"
    )
    config = pass_c.PassCConfig(
        citations_path=p3 / "pass_b_citations.jsonl",
        uc_drafts_path=p3 / "pass_a_use_case_drafts.jsonl",
        formal_path=p3 / "pass_c_formal.jsonl",
        formal_use_cases_path=p3 / "pass_c_formal_use_cases.jsonl",
        progress_path=p3 / "pass_c_progress.json",
        pass_b_progress_path=p3 / "pass_b_progress.json",
        project_type_path=project_type_path,
    )
    return pass_c.run_pass_c(config, resume=args.resume)


def _run_pass_d(args: argparse.Namespace, target_dir: Path) -> dict:
    p3 = _phase3_dir(target_dir)
    config = pass_d.PassDConfig(
        drafts_path=p3 / "pass_a_drafts.jsonl",
        uc_drafts_path=p3 / "pass_a_use_case_drafts.jsonl",
        formal_path=p3 / "pass_c_formal.jsonl",
        formal_use_cases_path=p3 / "pass_c_formal_use_cases.jsonl",
        sections_path=p3 / "pass_a_sections.json",
        audit_path=p3 / "pass_d_audit.json",
        section_coverage_path=p3 / "pass_d_section_coverage.json",
        council_inbox_path=p3 / "pass_d_council_inbox.json",
        progress_path=p3 / "pass_d_progress.json",
        pass_c_progress_path=p3 / "pass_c_progress.json",
    )
    return pass_d.run_pass_d(config, resume=args.resume)


def _main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    target_dir = args.target_dir.resolve()
    p3 = _phase3_dir(target_dir)
    p3.mkdir(parents=True, exist_ok=True)

    if args.pass_choice in ("A", "all"):
        print(f"=== Pass A: naive coverage on {target_dir} ===", file=sys.stderr)
        _run_pass_a(args, target_dir)

    if args.pass_choice in ("B", "all"):
        print("=== Pass B: mechanical citation extraction ===", file=sys.stderr)
        _run_pass_b(args, target_dir)

    if args.pass_choice in ("C", "all"):
        print("=== Pass C: formal REQ + UC production ===", file=sys.stderr)
        _run_pass_c(args, target_dir)

    if args.pass_choice in ("D", "all"):
        print("=== Pass D: coverage audit + council inbox ===", file=sys.stderr)
        summary = _run_pass_d(args, target_dir)
        print(f"Pass D summary: {summary}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(_main())
