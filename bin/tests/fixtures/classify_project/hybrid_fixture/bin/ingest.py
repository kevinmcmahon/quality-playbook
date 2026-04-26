"""ingest.py -- receipt ingestion orchestrator for the Hybrid fixture skill.

Walks a receipts folder, normalizes filenames, and emits per-receipt JSON
records. OCR is stubbed out -- the fixture's job is to provide enough code
LOC to push classification toward Hybrid, not to actually OCR images.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Iterable, Iterator, Optional


SUPPORTED_RECEIPT_EXTS = {".jpg", ".jpeg", ".png", ".pdf", ".heic"}
DEFAULT_OCR_CONFIDENCE_THRESHOLD = 0.85


@dataclass
class Receipt:
    source_path: str
    vendor: Optional[str]
    transaction_date: Optional[str]
    amount_cents: Optional[int]
    last_four: Optional[str]
    ocr_confidence: float
    needs_review: bool


def is_receipt_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_RECEIPT_EXTS


def discover_receipts(root: Path) -> Iterator[Path]:
    for current_root, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in names:
            p = Path(current_root) / name
            if is_receipt_file(p):
                yield p


def stub_ocr(path: Path) -> dict:
    """Return a stub OCR result keyed off the filename.

    Real implementation would call a vision model. The stub exists so the
    fixture has plausible code to count without pulling in heavy dependencies.
    """
    stem = path.stem.lower()
    parts = stem.split("_")
    vendor = parts[0] if parts else None
    transaction_date = None
    amount_cents = None
    last_four = None
    confidence = 0.5

    for part in parts[1:]:
        if part.isdigit() and len(part) == 8:
            transaction_date = f"{part[0:4]}-{part[4:6]}-{part[6:8]}"
            confidence += 0.2
        elif part.startswith("$") and part[1:].replace(".", "").isdigit():
            try:
                amount_cents = int(round(float(part[1:]) * 100))
                confidence += 0.2
            except ValueError:
                pass
        elif part.startswith("x") and part[1:].isdigit() and len(part) == 5:
            last_four = part[1:]
            confidence += 0.1

    confidence = min(confidence, 0.99)
    return {
        "vendor": vendor,
        "transaction_date": transaction_date,
        "amount_cents": amount_cents,
        "last_four": last_four,
        "ocr_confidence": confidence,
    }


def build_receipt(path: Path, threshold: float) -> Receipt:
    ocr = stub_ocr(path)
    needs_review = (
        ocr["ocr_confidence"] < threshold
        or ocr["transaction_date"] is None
        or ocr["amount_cents"] is None
    )
    return Receipt(
        source_path=str(path),
        vendor=ocr["vendor"],
        transaction_date=ocr["transaction_date"],
        amount_cents=ocr["amount_cents"],
        last_four=ocr["last_four"],
        ocr_confidence=ocr["ocr_confidence"],
        needs_review=needs_review,
    )


def ingest_directory(
    root: Path,
    *,
    confidence_threshold: float = DEFAULT_OCR_CONFIDENCE_THRESHOLD,
) -> list[Receipt]:
    receipts: list[Receipt] = []
    for path in discover_receipts(root):
        receipts.append(build_receipt(path, confidence_threshold))
    return receipts


def write_receipts_jsonl(receipts: Iterable[Receipt], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for r in receipts:
            fh.write(json.dumps(asdict(r), sort_keys=True) + "\n")


def split_receipts(receipts: Iterable[Receipt]) -> tuple[list[Receipt], list[Receipt]]:
    clean: list[Receipt] = []
    review: list[Receipt] = []
    for r in receipts:
        if r.needs_review:
            review.append(r)
        else:
            clean.append(r)
    return clean, review
