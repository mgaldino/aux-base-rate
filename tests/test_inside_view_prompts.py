from inside_view_harness import prompts


def test_inside_view_prompt_mentions_discrete_db_levels() -> None:
    text = prompts.EVIDENCE_DB_PROMPT
    assert "{10, 20, 30, 40}" in text


def test_inside_view_prompt_includes_examples() -> None:
    text = prompts.EVIDENCE_DB_PROMPT
    assert "EXAMPLE (weak)" in text
    assert "EXAMPLE (strong)" in text
