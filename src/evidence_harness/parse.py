import json
from typing import Optional, Tuple


_VALID_DB = {10, 20, 30, 40}


def parse_assignments_output(text: str) -> Tuple[Optional[list[dict]], Optional[str]]:
    if not text:
        return None, "empty_response"
    payload = _extract_json(text)
    if payload is None:
        return None, "invalid_json"
    assignments = payload.get("assignments") if isinstance(payload, dict) else None
    if assignments is None:
        return None, "missing_assignments"
    if not isinstance(assignments, list):
        return None, "invalid_assignments"
    for assignment in assignments:
        if not _valid_assignment(assignment):
            return None, "invalid_assignment"
    return assignments, None


def _valid_assignment(assignment: object) -> bool:
    if not isinstance(assignment, dict):
        return False
    if not assignment.get("article_id"):
        return False
    if not assignment.get("mechanism_id"):
        return False
    hypothesis = assignment.get("hypothesis")
    if hypothesis not in {"YES", "NO"}:
        return False
    direction = assignment.get("direction")
    if direction not in {"YES", "NO"}:
        return False
    evidence_db = assignment.get("evidence_db")
    if evidence_db not in _VALID_DB:
        return False
    novelty = assignment.get("novelty_score")
    if novelty is not None:
        try:
            float(novelty)
        except (TypeError, ValueError):
            return False
    return True


def _extract_json(text: str) -> Optional[dict]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
