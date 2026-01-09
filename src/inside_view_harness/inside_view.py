import math
from dataclasses import dataclass
from typing import Iterable

from inside_view_harness.parse import NormalizedEvidence


@dataclass(frozen=True)
class InsideViewConfig:
    strategy: str = "top_k"
    top_k: int = 3
    cap_db: float = 15.0
    source_repeat_discount: float = 0.5


def apply_inside_view(
    prior: float,
    mechanisms: Iterable[dict],
    evidence_items: Iterable[NormalizedEvidence],
    config: InsideViewConfig,
) -> tuple[float, list[dict]]:
    if prior <= 0 or prior >= 1:
        raise ValueError("prior must be between 0 and 1")

    evidence_by_mechanism: dict[str, list[NormalizedEvidence]] = {}
    for item in evidence_items:
        evidence_by_mechanism.setdefault(item.mechanism_id or "", []).append(item)

    by_mechanism: list[dict] = []
    total_effective_db = 0.0

    for mechanism in mechanisms:
        mechanism_id = mechanism.get("id")
        if not mechanism_id:
            continue
        items = evidence_by_mechanism.get(mechanism_id, [])
        if not items:
            continue
        raw_db = _sum_db(items)
        effective_db = _apply_strategy(items, raw_db, config)
        by_mechanism.append(
            {"mechanism_id": mechanism_id, "raw_db": raw_db, "effective_db": effective_db}
        )
        total_effective_db += effective_db

    updated_logit = _logit(prior) + total_effective_db * math.log(10) / 10.0
    posterior = _inv_logit(updated_logit)
    return posterior, by_mechanism


def _apply_strategy(
    items: list[NormalizedEvidence], raw_db: float, config: InsideViewConfig
) -> float:
    if config.strategy == "top_k":
        return _apply_top_k(items, config.top_k)
    if config.strategy == "source_discount":
        return _apply_source_discount(items, config.source_repeat_discount)
    if config.strategy == "cap":
        return max(-config.cap_db, min(config.cap_db, raw_db))
    raise ValueError(f"unknown strategy: {config.strategy}")


def _apply_top_k(items: list[NormalizedEvidence], top_k: int) -> float:
    weighted = [
        (item.evidence_db * item.novelty_score, item.direction) for item in items
    ]
    weighted.sort(key=lambda pair: pair[0], reverse=True)
    selected = weighted[: max(1, top_k)]
    return sum(weight * (1 if direction == "YES" else -1) for weight, direction in selected)


def _apply_source_discount(items: list[NormalizedEvidence], repeat_discount: float) -> float:
    by_source: dict[str, list[NormalizedEvidence]] = {}
    for item in items:
        source = item.source or f"__missing__:{item.evidence_id}"
        by_source.setdefault(source, []).append(item)

    total = 0.0
    for source_items in by_source.values():
        source_items.sort(key=lambda item: item.evidence_db * item.novelty_score, reverse=True)
        for idx, item in enumerate(source_items):
            weight = item.evidence_db * item.novelty_score
            if idx > 0:
                weight *= repeat_discount
            total += weight * (1 if item.direction == "YES" else -1)
    return total


def _sum_db(items: list[NormalizedEvidence]) -> float:
    return sum(
        item.evidence_db * item.novelty_score * (1 if item.direction == "YES" else -1)
        for item in items
    )


def _logit(p: float) -> float:
    return math.log(p / (1 - p))


def _inv_logit(x: float) -> float:
    return 1 / (1 + math.exp(-x))
