import json
from typing import Optional, Tuple


def parse_mechanisms_output(text: str) -> Tuple[Optional[dict], Optional[str]]:
    if not text:
        return None, "empty_response"
    payload = _extract_json(text)
    if payload is None:
        return None, "invalid_json"
    if not isinstance(payload, dict):
        return None, "invalid_json"
    mechanisms_yes = payload.get("mechanisms_yes")
    mechanisms_no = payload.get("mechanisms_no")
    if not isinstance(mechanisms_yes, list) or not isinstance(mechanisms_no, list):
        return None, "missing_mechanisms"
    if not mechanisms_yes and not mechanisms_no:
        return None, "missing_mechanisms"
    for mechanism in mechanisms_yes + mechanisms_no:
        if not isinstance(mechanism, dict):
            return None, "invalid_mechanism"
        if not mechanism.get("id") or not mechanism.get("label"):
            return None, "invalid_mechanism"
    return {"mechanisms_yes": mechanisms_yes, "mechanisms_no": mechanisms_no}, None


def _extract_json(text: str) -> Optional[dict]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
