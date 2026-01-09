from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional


def read_questions(path: str | Path) -> list[dict]:
    rows: list[dict] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                raise ValueError("invalid JSON line in questions file") from None
            rows.append(normalize_question(raw))
    return rows


def normalize_question(row: dict) -> dict:
    question_id = _pick_value(row, ["question_id", "id"])
    question = _pick_value(row, ["question", "title"])
    reference_date = _pick_reference_date(row)
    region = row.get("region") or _region_from_tags(row.get("tags"))
    notes = _build_notes(row)
    normalized = {
        "question_id": question_id,
        "question": question,
        "reference_date": reference_date,
        "region": region,
        "notes": notes,
    }
    if "outcome" in row:
        normalized["outcome"] = row.get("outcome")
    return normalized


def _pick_value(row: dict, keys: Iterable[str]) -> Optional[str]:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return str(value)
    return None


def _pick_reference_date(row: dict) -> Optional[str]:
    reference_date = row.get("reference_date")
    if reference_date:
        return _extract_date(str(reference_date))
    resolve_time = row.get("resolve_time")
    if resolve_time:
        return _extract_date(str(resolve_time))
    close_time = row.get("close_time")
    if close_time:
        return _extract_date(str(close_time))
    return None


def _extract_date(value: str) -> str:
    if "T" in value:
        return value.split("T", 1)[0]
    return value


def _region_from_tags(tags: object) -> Optional[str]:
    if not isinstance(tags, list):
        return None
    lower = {str(tag).strip().lower() for tag in tags}
    if "brasil" in lower or "brazil" in lower:
        return "Brasil"
    return None


def _build_notes(row: dict) -> Optional[str]:
    parts: list[str] = []
    description = row.get("description")
    if description:
        parts.append(str(description))
    resolution = row.get("resolution_criteria")
    if resolution:
        parts.append(str(resolution))
    if not parts:
        return row.get("notes")
    return " | ".join(parts)
