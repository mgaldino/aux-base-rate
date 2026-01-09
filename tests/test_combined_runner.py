import json
from pathlib import Path

from combined_harness.runner import run


class FakeClient:
    def generate(self, system, user, cfg):
        return "BASE_RATE: 50%\nRATIONALE: ok", None


def test_combined_runner_generates_prior_and_posterior(tmp_path: Path) -> None:
    questions_path = tmp_path / "questions.jsonl"
    mechanisms_path = tmp_path / "mechanisms.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    priors_output = tmp_path / "priors.jsonl"
    output_path = tmp_path / "posteriors.jsonl"

    with questions_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"question_id": "q1", "question": "Will X happen?"}) + "\n")

    with mechanisms_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"question_id": "q1", "mechanisms": [{"id": "m1"}]}) + "\n")

    with evidence_path.open("w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "evidence_id": "ev1",
                    "question_id": "q1",
                    "mechanism_id": "m1",
                    "direction": "YES",
                    "evidence_db": 10,
                    "novelty_score": 1.0,
                    "source": "manual",
                }
            )
            + "\n"
        )

    summary = run(
        questions_path=str(questions_path),
        mechanisms_path=str(mechanisms_path),
        evidence_path=str(evidence_path),
        priors_output_path=str(priors_output),
        output_path=str(output_path),
        model="test-model",
        prompt_ids=["v0"],
        temperature=0.2,
        client=FakeClient(),
    )

    assert summary["outside"]["n_records_written"] == 1
    assert summary["inside"]["n_records_written"] == 1

    with priors_output.open("r", encoding="utf-8") as f:
        priors_lines = [line for line in f if line.strip()]
    assert len(priors_lines) == 1

    with output_path.open("r", encoding="utf-8") as f:
        posterior = json.loads(f.readline())
    assert posterior["posterior"] > 0.5
