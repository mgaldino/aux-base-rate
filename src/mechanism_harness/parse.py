import json
from typing import Optional, Tuple


def parse_mechanisms_output(text: str) -> Tuple[Optional[list[dict]], Optional[str]]:
    if not text:
        return None, "empty_response"
    payload = _extract_json(text)
    if payload is None:
        return None, "invalid_json"
    mechanisms = payload.get("mechanisms") if isinstance(payload, dict) else None
    if not isinstance(mechanisms, list) or not mechanisms:
        return None, "missing_mechanisms"
    for mechanism in mechanisms:
        if not isinstance(mechanism, dict):
            return None, "invalid_mechanism"
        if not mechanism.get("id") or not mechanism.get("label"):
            return None, "invalid_mechanism"
    return mechanisms, None


def _extract_json(text: str) -> Optional[dict]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
