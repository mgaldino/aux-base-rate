from pathlib import Path

from base_rate_harness.io import read_jsonl, write_jsonl


def test_read_write_jsonl_roundtrip(tmp_path: Path) -> None:
    rows = [{"a": 1}, {"b": "two"}]
    path = tmp_path / "data.jsonl"
    count = write_jsonl(path, rows)
    assert count == 2
    loaded = read_jsonl(path)
    assert loaded == rows
