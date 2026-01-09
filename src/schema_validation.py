from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover - import-time guard
    raise ImportError(
        "jsonschema is required for schema validation. Install dependencies with "
        "`pip install -e '.[dev]'` or add jsonschema to your environment."
    ) from exc


def _default_schemas_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "schemas"


def load_schema(schema_name: str, schemas_dir: Optional[str] = None) -> dict:
    base = Path(schemas_dir) if schemas_dir else _default_schemas_dir()
    path = base / schema_name
    if not path.exists():
        raise FileNotFoundError(f"schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_rows(
    rows: Iterable[dict], schema_name: str, schemas_dir: Optional[str] = None
) -> None:
    schema = load_schema(schema_name, schemas_dir=schemas_dir)
    validator = Draft202012Validator(schema)
    for idx, row in enumerate(rows):
        errors = sorted(validator.iter_errors(row), key=lambda e: e.path)
        if errors:
            message = errors[0].message
            raise ValueError(
                "schema validation failed for {schema} at index {idx}: {message}".format(
                    schema=schema_name, idx=idx, message=message
                )
            )
