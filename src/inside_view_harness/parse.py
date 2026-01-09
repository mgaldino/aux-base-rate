import math
from dataclasses import dataclass
from typing import Optional, Tuple


_DIRECTION_MAP = {
    "YES": "YES",
    "Y": "YES",
    "TRUE": "YES",
    "SIM": "YES",
    "NO": "NO",
    "N": "NO",
    "FALSE": "NO",
    "NAO": "NO",
    "N\u00c3O": "NO",
}


@dataclass(frozen=True)
class NormalizedEvidence:
    evidence_id: Optional[str]
    question_id: Optional[str]
    mechanism_id: Optional[str]
    direction: str
    evidence_db: float
    novelty_score: float
    source: Optional[str]
    timestamp: Optional[str]
    notes: Optional[str]


def normalize_direction(value: object) -> Tuple[Optional[str], Optional[str]]:
    if value is None:
        return None, "missing_direction"
    if isinstance(value, bool):
        return ("YES" if value else "NO"), None
    text = str(value).strip()
    if not text:
        return None, "missing_direction"
    normalized = _DIRECTION_MAP.get(text.upper())
    if not normalized:
        return None, "invalid_direction"
    return normalized, None


def normalize_evidence(
    evidence: dict, mechanism_ids: set[str]
) -> Tuple[Optional[NormalizedEvidence], Optional[dict], list[dict]]:
    mechanism_id = evidence.get("mechanism_id")
    if not mechanism_id or mechanism_id not in mechanism_ids:
        return None, _discard_record(evidence, "missing_mechanism"), []

    direction, direction_reason = normalize_direction(evidence.get("direction"))
    if direction_reason:
        return None, _discard_record(evidence, direction_reason), []

    if "evidence_db" not in evidence or evidence.get("evidence_db") is None:
        return None, _discard_record(evidence, "missing_db"), []
    try:
        evidence_db = float(evidence.get("evidence_db"))
    except (TypeError, ValueError):
        return None, _discard_record(evidence, "invalid_db"), []
    if not math.isfinite(evidence_db):
        return None, _discard_record(evidence, "invalid_db"), []
    if evidence_db < 0:
        return None, _discard_record(evidence, "db_negative"), []
    if evidence_db < 10:
        return None, _discard_record(evidence, "db_below_threshold"), []

    novelty_score, adjustment, novelty_error = _normalize_novelty(evidence)
    if novelty_error:
        return None, _discard_record(evidence, novelty_error), []

    normalized = NormalizedEvidence(
        evidence_id=evidence.get("evidence_id"),
        question_id=evidence.get("question_id"),
        mechanism_id=mechanism_id,
        direction=direction,
        evidence_db=evidence_db,
        novelty_score=novelty_score,
        source=evidence.get("source"),
        timestamp=evidence.get("timestamp"),
        notes=evidence.get("notes"),
    )
    adjustments = [adjustment] if adjustment else []
    return normalized, None, adjustments


def _normalize_novelty(evidence: dict) -> Tuple[float, Optional[dict], Optional[str]]:
    raw_novelty = evidence.get("novelty_score")
    if raw_novelty is None:
        return 1.0, None, None
    try:
        novelty_score = float(raw_novelty)
    except (TypeError, ValueError):
        return 1.0, None, "invalid_novelty"
    clamped = min(1.0, max(0.0, novelty_score))
    if clamped == novelty_score:
        return novelty_score, None, None
    return clamped, _adjustment_record(evidence, "novelty_clamped", novelty_score, clamped), None


def _discard_record(evidence: dict, reason: str) -> dict:
    return {
        "evidence_id": evidence.get("evidence_id"),
        "question_id": evidence.get("question_id"),
        "mechanism_id": evidence.get("mechanism_id"),
        "reason": reason,
        "raw_direction": evidence.get("direction"),
        "evidence_db": evidence.get("evidence_db"),
        "novelty_score": evidence.get("novelty_score"),
        "source": evidence.get("source"),
        "timestamp": evidence.get("timestamp"),
        "notes": evidence.get("notes"),
    }


def _adjustment_record(
    evidence: dict, reason: str, raw_novelty_score: float, novelty_score: float
) -> dict:
    return {
        "evidence_id": evidence.get("evidence_id"),
        "question_id": evidence.get("question_id"),
        "mechanism_id": evidence.get("mechanism_id"),
        "reason": reason,
        "raw_novelty_score": raw_novelty_score,
        "novelty_score": novelty_score,
        "source": evidence.get("source"),
        "timestamp": evidence.get("timestamp"),
        "notes": evidence.get("notes"),
    }
