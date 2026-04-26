"""report.py -- reconciliation report assembler for the Hybrid fixture skill."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class ReconciliationSummary:
    matched_count: int
    unmatched_receipt_count: int
    unmatched_ledger_count: int
    review_queue_count: int
    total_amount_matched_cents: int


def cents_to_dollars(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    dollars, remainder = divmod(cents, 100)
    return f"{sign}${dollars:,}.{remainder:02d}"


def summarize(
    matched: Iterable[dict],
    unmatched_receipts: Iterable[dict],
    unmatched_ledger: Iterable[dict],
    review_queue: Iterable[dict],
) -> ReconciliationSummary:
    matched_list = list(matched)
    matched_total = sum(m.get("amount_cents") or 0 for m in matched_list)
    return ReconciliationSummary(
        matched_count=len(matched_list),
        unmatched_receipt_count=sum(1 for _ in unmatched_receipts),
        unmatched_ledger_count=sum(1 for _ in unmatched_ledger),
        review_queue_count=sum(1 for _ in review_queue),
        total_amount_matched_cents=matched_total,
    )


def render_markdown(summary: ReconciliationSummary, *, period_label: str) -> str:
    lines = [
        f"# Reconciliation report -- {period_label}",
        "",
        "## Summary",
        "",
        f"- Matched receipts: {summary.matched_count}",
        f"- Total amount matched: {cents_to_dollars(summary.total_amount_matched_cents)}",
        f"- Unmatched receipts: {summary.unmatched_receipt_count}",
        f"- Unmatched ledger entries: {summary.unmatched_ledger_count}",
        f"- Receipts awaiting human review: {summary.review_queue_count}",
        "",
        "## What to look at first",
        "",
    ]
    if summary.unmatched_receipt_count:
        lines.append(
            "- Unmatched receipts -- the team paid for something the ledger "
            "doesn't know about; investigate before booking the period closed."
        )
    if summary.unmatched_ledger_count:
        lines.append(
            "- Unmatched ledger entries -- the bookkeeping shows charges the "
            "receipts folder doesn't cover; missing receipt or duplicate post."
        )
    if summary.review_queue_count:
        lines.append(
            "- Human-review queue -- OCR confidence was low or fields were "
            "missing; these need an operator pass before re-running matching."
        )
    if (
        summary.unmatched_receipt_count == 0
        and summary.unmatched_ledger_count == 0
        and summary.review_queue_count == 0
    ):
        lines.append("- Clean reconciliation. No follow-up required.")
    return "\n".join(lines) + "\n"


def write_report(out_path, summary: ReconciliationSummary, period_label: str) -> None:
    rendered = render_markdown(summary, period_label=period_label)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")
