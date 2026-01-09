import json
import math
from pathlib import Path

import pytest

from inside_view_harness import inside_view, parse, runner


def test_normalize_direction_accepts_variants() -> None:
    for raw, expected in [
        ("YES", "YES"),
        ("yes", "YES"),
        ("SIM", "YES"),
        ("true", "YES"),
        ("NO", "NO"),
        ("nao", "NO"),
        ("FALSE", "NO"),
    ]:
        value, reason = parse.normalize_direction(raw)
        assert reason is None
        assert value == expected


def test_normalize_direction_rejects_invalid_and_missing() -> None:
    value, reason = parse.normalize_direction(None)
    assert value is None
    assert reason == "missing_direction"

    value, reason = parse.normalize_direction("MAYBE")
    assert value is None
    assert reason == "invalid_direction"


def test_normalize_evidence_discards_invalid_db() -> None:
    evidence = {
        "evidence_id": "ev1",
        "question_id": "q1",
        "mechanism_id": "m1",
        "direction": "YES",
        "evidence_db": 5,
        "novelty_score": 1.0,
        "source": "news",
        "timestamp": "2023-01-01T00:00:00Z",
        "notes": "low db",
    }
    normalized, discard, adjustments = parse.normalize_evidence(evidence, {"m1"})
    assert normalized is None
    assert discard is not None
    assert discard["reason"] == "db_below_threshold"
    assert adjustments == []


def test_normalize_evidence_discards_missing_or_invalid_db() -> None:
    missing_db = {
        "evidence_id": "ev_missing",
        "question_id": "q1",
        "mechanism_id": "m1",
        "direction": "YES",
        "source": "news",
    }
    normalized, discard, adjustments = parse.normalize_evidence(missing_db, {"m1"})
    assert normalized is None
    assert discard is not None
    assert discard["reason"] == "missing_db"
    assert adjustments == []

    invalid_db = {
        "evidence_id": "ev_invalid",
        "question_id": "q1",
        "mechanism_id": "m1",
        "direction": "YES",
        "evidence_db": "NaN",
        "source": "news",
    }
    normalized, discard, adjustments = parse.normalize_evidence(invalid_db, {"m1"})
    assert normalized is None
    assert discard is not None
    assert discard["reason"] == "invalid_db"
    assert adjustments == []


def test_normalize_evidence_discards_invalid_novelty() -> None:
    evidence = {
        "evidence_id": "ev_bad_novelty",
        "question_id": "q1",
        "mechanism_id": "m1",
        "direction": "YES",
        "evidence_db": 12,
        "novelty_score": "oops",
        "source": "news",
    }
    normalized, discard, adjustments = parse.normalize_evidence(evidence, {"m1"})
    assert normalized is None
    assert discard is not None
    assert discard["reason"] == "invalid_novelty"
    assert adjustments == []

def test_normalize_evidence_clamps_novelty() -> None:
    evidence = {
        "evidence_id": "ev2",
        "question_id": "q1",
        "mechanism_id": "m1",
        "direction": "YES",
        "evidence_db": 12,
        "novelty_score": 1.2,
        "source": "news",
        "timestamp": "2023-01-01T00:00:00Z",
        "notes": "high novelty",
    }
    normalized, discard, adjustments = parse.normalize_evidence(evidence, {"m1"})
    assert discard is None
    assert normalized is not None
    assert normalized.novelty_score == 1.0
    assert len(adjustments) == 1
    assert adjustments[0]["reason"] == "novelty_clamped"


def test_apply_inside_view_top_k_and_logit() -> None:
    mechanisms = [{"id": "m1"}, {"id": "m2"}]
    evidence_items = [
        parse.NormalizedEvidence(
            evidence_id="ev1",
            question_id="q1",
            mechanism_id="m1",
            direction="YES",
            evidence_db=10.0,
            novelty_score=1.0,
            source="news",
            timestamp=None,
            notes=None,
        ),
        parse.NormalizedEvidence(
            evidence_id="ev2",
            question_id="q1",
            mechanism_id="m1",
            direction="YES",
            evidence_db=10.0,
            novelty_score=1.0,
            source="news",
            timestamp=None,
            notes=None,
        ),
        parse.NormalizedEvidence(
            evidence_id="ev3",
            question_id="q1",
            mechanism_id="m1",
            direction="YES",
            evidence_db=10.0,
            novelty_score=1.0,
            source="news",
            timestamp=None,
            notes=None,
        ),
        parse.NormalizedEvidence(
            evidence_id="ev4",
            question_id="q1",
            mechanism_id="m1",
            direction="YES",
            evidence_db=10.0,
            novelty_score=1.0,
            source="news",
            timestamp=None,
            notes=None,
        ),
        parse.NormalizedEvidence(
            evidence_id="ev5",
            question_id="q1",
            mechanism_id="m2",
            direction="NO",
            evidence_db=10.0,
            novelty_score=1.0,
            source="news",
            timestamp=None,
            notes=None,
        ),
    ]
    cfg = inside_view.InsideViewConfig(strategy="top_k", top_k=3, cap_db=15.0)
    posterior, by_mech = inside_view.apply_inside_view(0.5, mechanisms, evidence_items, cfg)

    expected_update = 20.0 * math.log(10) / 10.0
    expected_posterior = 1 / (1 + math.exp(-expected_update))

    assert math.isclose(posterior, expected_posterior, rel_tol=1e-6)
    assert len(by_mech) == 2
    m1 = next(item for item in by_mech if item["mechanism_id"] == "m1")
    assert m1["raw_db"] == 40.0
    assert m1["effective_db"] == 30.0


def test_runner_writes_logs(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"
    discard_path = tmp_path / "discard.jsonl"
    adjust_path = tmp_path / "adjust.jsonl"

    with priors_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"question_id": "q1", "prompt_id": "v0", "base_rate": 50.0}) + "\n")

    with mechanisms_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"question_id": "q1", "mechanisms": [{"id": "m1"}]}) + "\n")

    evidence_rows = [
        {
            "evidence_id": "ev1",
            "question_id": "q1",
            "mechanism_id": "m1",
            "direction": "YES",
            "evidence_db": 5,
            "novelty_score": 1.0,
            "source": "news",
            "timestamp": "2023-01-01T00:00:00Z",
            "notes": "discard",
        },
        {
            "evidence_id": "ev2",
            "question_id": "q1",
            "mechanism_id": "m1",
            "direction": "YES",
            "evidence_db": 12,
            "novelty_score": 1.2,
            "source": "news",
            "timestamp": "2023-01-01T00:00:00Z",
            "notes": "adjust",
        },
    ]
    with evidence_path.open("w", encoding="utf-8") as f:
        for row in evidence_rows:
            f.write(json.dumps(row) + "\n")

    summary = runner.run(
        priors_path=str(priors_path),
        mechanisms_path=str(mechanisms_path),
        evidence_path=str(evidence_path),
        output_path=str(output_path),
        discard_log_path=str(discard_path),
        adjustment_log_path=str(adjust_path),
    )

    assert summary["n_records_written"] == 1
    assert summary["n_discards"] == 1
    assert summary["n_adjustments"] == 1

    with discard_path.open("r", encoding="utf-8") as f:
        discard_lines = [line for line in f if line.strip()]
    assert len(discard_lines) == 1

    with adjust_path.open("r", encoding="utf-8") as f:
        adjust_lines = [line for line in f if line.strip()]
    assert len(adjust_lines) == 1
