import json
from pathlib import Path


def _load_schema(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_schema_files_exist_and_have_required_fields() -> None:
    base = Path("schemas")
    required_files = [
        "questions.schema.json",
        "priors.schema.json",
        "mechanisms.schema.json",
        "evidence.schema.json",
        "outside_view_output.schema.json",
        "inside_view_output.schema.json",
        "discard_log.schema.json",
        "adjustment_log.schema.json",
    ]
    for name in required_files:
        schema = _load_schema(base / name)
        assert "$schema" in schema
        assert "type" in schema
        assert schema["type"] == "object"
        assert "required" in schema
