import json

from mechanism_harness.parse import parse_mechanisms_output


def test_parse_mechanisms_output_accepts_valid_json() -> None:
    payload = {
        "mechanisms": [
            {"id": "m1_quality", "label": "quality of accusation", "prior_weight": 0.4},
            {"id": "m2_speed", "label": "court speed", "prior_weight": 0.3},
        ]
    }
    text = json.dumps(payload)
    mechanisms, error = parse_mechanisms_output(text)
    assert error is None
    assert mechanisms is not None
    assert len(mechanisms) == 2
    assert mechanisms[0]["id"] == "m1_quality"


def test_parse_mechanisms_output_rejects_missing_fields() -> None:
    payload = {"mechanisms": [{"label": "missing id"}]}
    text = json.dumps(payload)
    mechanisms, error = parse_mechanisms_output(text)
    assert mechanisms is None
    assert error == "invalid_mechanism"
