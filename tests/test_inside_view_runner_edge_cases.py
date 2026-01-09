import json
import math
from pathlib import Path

import pytest

from inside_view_harness import runner


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_runner_raises_on_missing_base_rate(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"

    _write_jsonl(
        priors_path, [{"question_id": "q1", "prompt_id": "v0", "base_rate": None}]
    )
    _write_jsonl(mechanisms_path, [{"question_id": "q1", "mechanisms": [{"id": "m1"}]}])
    _write_jsonl(evidence_path, [])

    with pytest.raises(ValueError, match="missing base_rate"):
        runner.run(
            priors_path=str(priors_path),
            mechanisms_path=str(mechanisms_path),
            evidence_path=str(evidence_path),
            output_path=str(output_path),
        )


def test_runner_raises_on_missing_mechanisms(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"

    _write_jsonl(priors_path, [{"question_id": "q1", "prompt_id": "v0", "base_rate": 30}])
    _write_jsonl(mechanisms_path, [])
    _write_jsonl(evidence_path, [])

    with pytest.raises(ValueError, match="missing mechanisms"):
        runner.run(
            priors_path=str(priors_path),
            mechanisms_path=str(mechanisms_path),
            evidence_path=str(evidence_path),
            output_path=str(output_path),
        )


def test_runner_raises_on_mechanism_missing_id(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"

    _write_jsonl(priors_path, [{"question_id": "q1", "prompt_id": "v0", "base_rate": 30}])
    _write_jsonl(
        mechanisms_path,
        [{"question_id": "q1", "mechanisms": [{"label": "missing id"}]}],
    )
    _write_jsonl(evidence_path, [])

    with pytest.raises(ValueError, match="missing mechanism id"):
        runner.run(
            priors_path=str(priors_path),
            mechanisms_path=str(mechanisms_path),
            evidence_path=str(evidence_path),
            output_path=str(output_path),
        )


def test_runner_accepts_case_insensitive_question_ids(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"

    _write_jsonl(priors_path, [{"question_id": "q1", "prompt_id": "v0", "base_rate": 50}])
    _write_jsonl(
        mechanisms_path,
        [{"question_id": "Q1", "mechanisms": [{"id": "m1"}]}],
    )
    _write_jsonl(
        evidence_path,
        [
            {
                "evidence_id": "ev1",
                "question_id": "q1",
                "mechanism_id": "m1",
                "direction": "YES",
                "evidence_db": 10,
            }
        ],
    )

    runner.run(
        priors_path=str(priors_path),
        mechanisms_path=str(mechanisms_path),
        evidence_path=str(evidence_path),
        output_path=str(output_path),
    )

    with output_path.open("r", encoding="utf-8") as f:
        record = json.loads(f.readline())
    assert record["question_id"] == "q1"
    assert record["by_mechanism"][0]["raw_db"] == 10.0


def test_runner_rejects_question_id_collision(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"

    _write_jsonl(
        priors_path,
        [
            {"question_id": "q1", "prompt_id": "v0", "base_rate": 50},
            {"question_id": "Q1", "prompt_id": "v1", "base_rate": 50},
        ],
    )
    _write_jsonl(
        mechanisms_path,
        [{"question_id": "q1", "mechanisms": [{"id": "m1"}]}],
    )
    _write_jsonl(evidence_path, [])

    with pytest.raises(ValueError, match="question_id collision"):
        runner.run(
            priors_path=str(priors_path),
            mechanisms_path=str(mechanisms_path),
            evidence_path=str(evidence_path),
            output_path=str(output_path),
        )


def test_runner_keeps_prior_without_evidence(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"

    _write_jsonl(priors_path, [{"question_id": "q1", "prompt_id": "v0", "base_rate": 30}])
    _write_jsonl(mechanisms_path, [{"question_id": "q1", "mechanisms": [{"id": "m1"}]}])
    _write_jsonl(evidence_path, [])

    summary = runner.run(
        priors_path=str(priors_path),
        mechanisms_path=str(mechanisms_path),
        evidence_path=str(evidence_path),
        output_path=str(output_path),
    )
    assert summary["n_records_written"] == 1

    with output_path.open("r", encoding="utf-8") as f:
        record = json.loads(f.readline())
    assert math.isclose(record["prior"], 0.3, rel_tol=1e-9)
    assert math.isclose(record["posterior"], 0.3, rel_tol=1e-9)


def test_runner_rejects_out_of_bounds_base_rate(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"

    _write_jsonl(
        priors_path,
        [
            {"question_id": "q1", "prompt_id": "v0", "base_rate": -1},
        ],
    )
    _write_jsonl(mechanisms_path, [{"question_id": "q1", "mechanisms": [{"id": "m1"}]}])
    _write_jsonl(evidence_path, [])

    with pytest.raises(ValueError, match="base_rate_out_of_bounds"):
        runner.run(
            priors_path=str(priors_path),
            mechanisms_path=str(mechanisms_path),
            evidence_path=str(evidence_path),
            output_path=str(output_path),
        )


def test_runner_rejects_extreme_base_rate(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"

    _write_jsonl(
        priors_path,
        [
            {"question_id": "q1", "prompt_id": "v0", "base_rate": 100},
        ],
    )
    _write_jsonl(mechanisms_path, [{"question_id": "q1", "mechanisms": [{"id": "m1"}]}])
    _write_jsonl(evidence_path, [])

    with pytest.raises(ValueError, match="base_rate_out_of_bounds"):
        runner.run(
            priors_path=str(priors_path),
            mechanisms_path=str(mechanisms_path),
            evidence_path=str(evidence_path),
            output_path=str(output_path),
        )


def test_runner_uses_provided_run_ts(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"

    _write_jsonl(priors_path, [{"question_id": "q1", "prompt_id": "v0", "base_rate": 50}])
    _write_jsonl(mechanisms_path, [{"question_id": "q1", "mechanisms": [{"id": "m1"}]}])
    _write_jsonl(evidence_path, [])

    run_ts = "2025-01-01T00:00:00Z"
    runner.run(
        priors_path=str(priors_path),
        mechanisms_path=str(mechanisms_path),
        evidence_path=str(evidence_path),
        output_path=str(output_path),
        run_ts=run_ts,
    )

    with output_path.open("r", encoding="utf-8") as f:
        record = json.loads(f.readline())
    assert record["meta"]["run_ts"] == run_ts


def test_runner_schema_validation_catches_missing_evidence_id(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"

    _write_jsonl(priors_path, [{"question_id": "q1", "prompt_id": "v0", "base_rate": 50}])
    _write_jsonl(mechanisms_path, [{"question_id": "q1", "mechanisms": [{"id": "m1"}]}])
    _write_jsonl(
        evidence_path,
        [
            {
                "question_id": "q1",
                "mechanism_id": "m1",
                "direction": "YES",
                "evidence_db": 10,
            }
        ],
    )

    with pytest.raises(ValueError, match="schema validation failed"):
        runner.run(
            priors_path=str(priors_path),
            mechanisms_path=str(mechanisms_path),
            evidence_path=str(evidence_path),
            output_path=str(output_path),
            validate_schemas=True,
        )


def test_runner_computes_posterior_odds_with_yes_no_mechanisms(tmp_path: Path) -> None:
    priors_path = tmp_path / "priors.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    output_path = tmp_path / "output.jsonl"

    _write_jsonl(priors_path, [{"question_id": "q1", "prompt_id": "v0", "base_rate": 50}])
    _write_jsonl(
        mechanisms_path,
        [
            {
                "question_id": "q1",
                "mechanisms_yes": [{"id": "m1_yes"}],
                "mechanisms_no": [{"id": "m1_no"}],
            }
        ],
    )
    _write_jsonl(
        evidence_path,
        [
            {
                "evidence_id": "ev_yes",
                "question_id": "q1",
                "mechanism_id": "m1_yes",
                "hypothesis": "YES",
                "direction": "YES",
                "evidence_db": 20,
            },
            {
                "evidence_id": "ev_no",
                "question_id": "q1",
                "mechanism_id": "m1_no",
                "hypothesis": "NO",
                "direction": "YES",
                "evidence_db": 10,
            },
        ],
    )

    runner.run(
        priors_path=str(priors_path),
        mechanisms_path=str(mechanisms_path),
        evidence_path=str(evidence_path),
        output_path=str(output_path),
    )

    with output_path.open("r", encoding="utf-8") as f:
        record = json.loads(f.readline())
    assert record["posterior_odds"] == 10.0
    assert record["posterior"] == 10.0 / 11.0
