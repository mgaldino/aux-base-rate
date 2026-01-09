import json
from pathlib import Path

import pytest

from base_rate_harness.runner import run


class FakeClient:
    def generate(self, system, user, cfg):
        return "BASE_RATE: 50%\nRATIONALE: ok", None


def test_runner_generates_expected_number_of_rows_for_small_input(tmp_path: Path) -> None:
    questions = [
        {"question_id": "q1", "question": "Will X happen?"},
        {"question_id": "q2", "question": "Will Y happen?"},
    ]
    input_path = tmp_path / "questions.jsonl"
    with input_path.open("w", encoding="utf-8") as f:
        for row in questions:
            f.write(json.dumps(row) + "\n")

    output_path = tmp_path / "results.jsonl"
    summary = run(
        input_path=str(input_path),
        output_path=str(output_path),
        model="test-model",
        prompt_ids=["v0", "v0_2"],
        temperature=0.2,
        client=FakeClient(),
    )

    assert summary["n_records_written"] == 4
    assert summary["n_parse_failures"] == 0
    assert summary["n_call_failures"] == 0

    with output_path.open("r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    assert len(lines) == 4


def test_runner_rejects_missing_required_fields(tmp_path: Path) -> None:
    questions = [
        {"question_id": "q1", "question": "Will X happen?"},
        {"question_id": None, "question": "Missing id"},
    ]
    input_path = tmp_path / "questions.jsonl"
    with input_path.open("w", encoding="utf-8") as f:
        for row in questions:
            f.write(json.dumps(row) + "\n")

    output_path = tmp_path / "results.jsonl"
    with pytest.raises(ValueError, match="missing question_id"):
        run(
            input_path=str(input_path),
            output_path=str(output_path),
            model="test-model",
            prompt_ids=["v0"],
            temperature=0.2,
            client=FakeClient(),
        )


def test_runner_rejects_missing_question_text(tmp_path: Path) -> None:
    questions = [
        {"question_id": "q1", "question": None},
    ]
    input_path = tmp_path / "questions.jsonl"
    with input_path.open("w", encoding="utf-8") as f:
        for row in questions:
            f.write(json.dumps(row) + "\n")

    output_path = tmp_path / "results.jsonl"
    with pytest.raises(ValueError, match="missing question"):
        run(
            input_path=str(input_path),
            output_path=str(output_path),
            model="test-model",
            prompt_ids=["v0"],
            temperature=0.2,
            client=FakeClient(),
        )
