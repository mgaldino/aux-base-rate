from base_rate_harness.prompts import default_registry, render_user_prompt


def test_prompt_rendering_includes_optional_fields_as_NA() -> None:
    registry = default_registry()
    variant = registry["v0"]
    question = {"question_id": "q1", "question": "Will X happen?"}
    rendered = render_user_prompt(variant, question)
    assert "Reference date: N/A" in rendered
    assert "Region: N/A" in rendered
    assert "Notes: N/A" in rendered
