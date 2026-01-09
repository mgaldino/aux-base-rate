from evidence_harness.prompts import USER_PROMPT


def test_evidence_prompt_formatting() -> None:
    rendered = USER_PROMPT.format(
        question_id="q1",
        question="Will X happen?",
        reference_date="2025-01-01",
        region="Brasil",
        notes="notes",
        mechanisms="m1: mech",
        articles="a1: title",
    )
    assert "{10, 20, 30, 40}" in rendered
