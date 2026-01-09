import json

from evidence_harness.gdelt import build_gdelt_url, parse_gdelt_response


def test_build_gdelt_url_includes_query() -> None:
    url = build_gdelt_url("bolsonaro AND tse", max_records=5, timespan="1m")
    assert "query=bolsonaro+AND+tse" in url
    assert "maxrecords=5" in url
    assert "timespan=1m" in url


def test_build_gdelt_url_accepts_date_range() -> None:
    url = build_gdelt_url(
        "bolsonaro",
        max_records=5,
        start_datetime="20240101000000",
        end_datetime="20240131235959",
    )
    assert "startdatetime=20240101000000" in url
    assert "enddatetime=20240131235959" in url
    assert "timespan" not in url


def test_parse_gdelt_response_extracts_articles() -> None:
    payload = {
        "articles": [
            {
                "url": "https://example.com/a",
                "title": "Example title",
                "seendate": "20250101000000",
                "sourcecountry": "BR",
            }
        ]
    }
    articles = parse_gdelt_response(json.dumps(payload))
    assert len(articles) == 1
    assert articles[0]["url"] == "https://example.com/a"
