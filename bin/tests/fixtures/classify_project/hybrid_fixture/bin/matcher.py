"""matcher.py -- candidate match generator for the Hybrid fixture skill."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Optional


@dataclass
class LedgerEntry:
    entry_id: str
    vendor: Optional[str]
    posted_date: Optional[str]
    amount_cents: Optional[int]
    last_four: Optional[str]


@dataclass
class CandidateMatch:
    receipt_path: str
    ledger_entry_id: str
    score: float
    rationale: str


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def date_proximity_score(
    receipt_date: Optional[str],
    ledger_date: Optional[str],
    *,
    max_days: int = 7,
) -> float:
    rd = parse_iso_date(receipt_date)
    ld = parse_iso_date(ledger_date)
    if rd is None or ld is None:
        return 0.0
    delta_days = abs((rd - ld).days)
    if delta_days > max_days:
        return 0.0
    return 1.0 - (delta_days / max_days)


def amount_similarity_score(
    receipt_cents: Optional[int],
    ledger_cents: Optional[int],
    *,
    tolerance_cents: int = 100,
) -> float:
    if receipt_cents is None or ledger_cents is None:
        return 0.0
    delta = abs(receipt_cents - ledger_cents)
    if delta == 0:
        return 1.0
    if delta > tolerance_cents:
        return 0.0
    return 1.0 - (delta / tolerance_cents)


def vendor_match_score(receipt_vendor: Optional[str], ledger_vendor: Optional[str]) -> float:
    if not receipt_vendor or not ledger_vendor:
        return 0.0
    rv = receipt_vendor.strip().lower()
    lv = ledger_vendor.strip().lower()
    if rv == lv:
        return 1.0
    if rv in lv or lv in rv:
        return 0.6
    rv_tokens = set(rv.split())
    lv_tokens = set(lv.split())
    if not rv_tokens or not lv_tokens:
        return 0.0
    overlap = rv_tokens & lv_tokens
    return len(overlap) / max(len(rv_tokens), len(lv_tokens))


def last_four_match(receipt_last_four: Optional[str], ledger_last_four: Optional[str]) -> bool:
    if not receipt_last_four or not ledger_last_four:
        return False
    return receipt_last_four == ledger_last_four


def combined_score(receipt: dict, ledger: LedgerEntry) -> tuple[float, str]:
    date_score = date_proximity_score(receipt.get("transaction_date"), ledger.posted_date)
    amount_score = amount_similarity_score(receipt.get("amount_cents"), ledger.amount_cents)
    vendor_score = vendor_match_score(receipt.get("vendor"), ledger.vendor)
    last_four_bonus = 0.1 if last_four_match(receipt.get("last_four"), ledger.last_four) else 0.0

    score = (date_score * 0.35) + (amount_score * 0.40) + (vendor_score * 0.25) + last_four_bonus
    rationale = (
        f"date={date_score:.2f}, amount={amount_score:.2f}, "
        f"vendor={vendor_score:.2f}, last4_bonus={last_four_bonus:.2f}"
    )
    return score, rationale


def top_k_matches(
    receipt: dict,
    ledger_entries: Iterable[LedgerEntry],
    *,
    k: int = 3,
    min_score: float = 0.3,
) -> list[CandidateMatch]:
    scored: list[CandidateMatch] = []
    for entry in ledger_entries:
        score, rationale = combined_score(receipt, entry)
        if score < min_score:
            continue
        scored.append(
            CandidateMatch(
                receipt_path=receipt.get("source_path", ""),
                ledger_entry_id=entry.entry_id,
                score=score,
                rationale=rationale,
            )
        )
    scored.sort(key=lambda m: m.score, reverse=True)
    return scored[:k]
