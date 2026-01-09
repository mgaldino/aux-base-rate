import json
from pathlib import Path

from reporting.report import build_report, render_html


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_report_includes_brier_scores_with_outcomes(tmp_path: Path) -> None:
    outside_path = tmp_path / "outside.jsonl"
    inside_path = tmp_path / "inside.jsonl"
    questions_path = tmp_path / "questions.jsonl"

    _write_jsonl(
        outside_path,
        [
            {
                "question_id": "q1",
                "prompt_id": "v0",
                "base_rate": 70.0,
                "parse_error": None,
                "call_error": None,
                "meta": {"model": "test-model"},
            }
        ],
    )
    _write_jsonl(
        inside_path,
        [
            {
                "question_id": "q1",
                "prompt_id": "v0",
                "prior": 0.7,
                "posterior": 0.8,
                "by_mechanism": [],
                "meta": {"run_ts": "2025-01-01T00:00:00Z", "version": "inside_view_v1"},
            }
        ],
    )
    _write_jsonl(
        questions_path,
        [
            {"question_id": "q1", "question": "Will X happen?", "outcome": "YES"},
        ],
    )

    report = build_report(
        outside_paths=[outside_path],
        inside_paths=[inside_path],
        questions_path=questions_path,
    )
    html = render_html(report)
    assert "Brier" in html
    assert "0.0900" in html
    assert "0.0400" in html
    assert "test-model" in html


def test_report_handles_missing_outcomes(tmp_path: Path) -> None:
    outside_path = tmp_path / "outside.jsonl"
    _write_jsonl(
        outside_path,
        [
            {
                "question_id": "q1",
                "prompt_id": "v0",
                "base_rate": 50.0,
                "parse_error": None,
                "call_error": None,
            }
        ],
    )
    report = build_report(outside_paths=[outside_path], inside_paths=[], questions_path=None)
    html = render_html(report)
    assert "Brier" not in html


def test_report_includes_question_details(tmp_path: Path) -> None:
    outside_path = tmp_path / "outside.jsonl"
    inside_path = tmp_path / "inside.jsonl"
    questions_path = tmp_path / "questions.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"

    _write_jsonl(
        outside_path,
        [
            {
                "question_id": "q1",
                "prompt_id": "v0",
                "base_rate": 60.0,
                "parse_error": None,
                "call_error": None,
            }
        ],
    )
    _write_jsonl(
        inside_path,
        [
            {
                "question_id": "q1",
                "prompt_id": "v0",
                "prior": 0.6,
                "posterior": 0.7,
                "by_mechanism": [],
                "meta": {"run_ts": "2025-01-01T00:00:00Z", "version": "inside_view_v1"},
            }
        ],
    )
    _write_jsonl(
        questions_path,
        [
            {"question_id": "q1", "question": "Will X happen?"},
        ],
    )
    _write_jsonl(
        mechanisms_path,
        [
            {
                "question_id": "q1",
                "mechanisms": [{"id": "m1", "label": "mechanism one"}],
            }
        ],
    )
    _write_jsonl(
        evidence_path,
        [
            {
                "evidence_id": "ev1",
                "question_id": "q1",
                "mechanism_id": "m1",
                "direction": "YES",
                "evidence_db": 20,
                "summary": "Evidence summary",
            }
        ],
    )

    report = build_report(
        outside_paths=[outside_path],
        inside_paths=[inside_path],
        questions_path=questions_path,
        mechanisms_path=mechanisms_path,
        evidence_path=evidence_path,
    )
    html = render_html(report)
    assert "Will X happen?" in html
    assert "mechanism one" in html
    assert "Evidence summary" in html
