import json

from mechanism_harness.parse import parse_mechanisms_output


def test_parse_mechanisms_output_accepts_valid_json() -> None:
    payload = {
        "mechanisms_yes": [
            {"id": "m1_quality", "label": "quality of accusation", "prior_weight": 0.4},
            {"id": "m2_speed", "label": "court speed", "prior_weight": 0.3},
        ],
        "mechanisms_no": [
            {"id": "m1_delay", "label": "delays or dismissals", "prior_weight": 0.5},
        ],
    }
    text = json.dumps(payload)
    mechanisms, error = parse_mechanisms_output(text)
    assert error is None
    assert mechanisms is not None
    assert len(mechanisms["mechanisms_yes"]) == 2
    assert mechanisms["mechanisms_yes"][0]["id"] == "m1_quality"


def test_parse_mechanisms_output_rejects_missing_fields() -> None:
    payload = {"mechanisms_yes": [{"label": "missing id"}], "mechanisms_no": []}
    text = json.dumps(payload)
    mechanisms, error = parse_mechanisms_output(text)
    assert mechanisms is None
    assert error == "invalid_mechanism"
