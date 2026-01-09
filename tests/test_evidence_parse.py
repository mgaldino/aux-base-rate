import json

from evidence_harness.parse import parse_assignments_output


def test_parse_assignments_output_accepts_valid_json() -> None:
    payload = {
        "assignments": [
            {
                "article_id": "a1",
                "mechanism_id": "m1_quality",
                "direction": "YES",
                "evidence_db": 20,
                "novelty_score": 0.8,
                "notes": "supports mechanism",
            }
        ]
    }
    text = json.dumps(payload)
    assignments, error = parse_assignments_output(text)
    assert error is None
    assert assignments is not None
    assert assignments[0]["article_id"] == "a1"


def test_parse_assignments_output_rejects_invalid_db() -> None:
    payload = {
        "assignments": [
            {
                "article_id": "a1",
                "mechanism_id": "m1_quality",
                "direction": "YES",
                "evidence_db": 15,
            }
        ]
    }
    text = json.dumps(payload)
    assignments, error = parse_assignments_output(text)
    assert assignments is None
    assert error == "invalid_assignment"
