from pathlib import Path

from question_io import read_questions


def test_read_questions_normalizes_json_test_format(tmp_path: Path) -> None:
    content = (
        "# Header line\n"
        '{"id":"BR_Q005","title":"Pergunta X","description":"Desc","resolution_criteria":"Crit",'
        '"close_time":"2023-06-29T23:59:00-03:00","resolve_time":"2023-06-30T20:30:00-03:00",'
        '"outcome":"YES","tags":["brasil","tse"]}\n'
    )
    path = tmp_path / "JSON_TEST.md"
    path.write_text(content, encoding="utf-8")

    rows = read_questions(path)
    assert len(rows) == 1
    row = rows[0]
    assert row["question_id"] == "BR_Q005"
    assert row["question"] == "Pergunta X"
    assert row["reference_date"] == "2023-06-30"
    assert row["region"] == "Brasil"
    assert "Desc" in row["notes"]
    assert "Crit" in row["notes"]
    assert row["outcome"] == "YES"
