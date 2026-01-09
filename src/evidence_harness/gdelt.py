from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Optional


GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


def build_gdelt_url(
    query: str,
    max_records: int = 50,
    timespan: str = "7d",
    mode: str = "ArtList",
    fmt: str = "json",
    start_datetime: Optional[str] = None,
    end_datetime: Optional[str] = None,
) -> str:
    params = {
        "query": query,
        "mode": mode,
        "format": fmt,
        "maxrecords": max_records,
    }
    if start_datetime and end_datetime:
        params["startdatetime"] = start_datetime
        params["enddatetime"] = end_datetime
    else:
        params["timespan"] = timespan
    return "{}?{}".format(GDELT_DOC_API, urllib.parse.urlencode(params))


def fetch_gdelt_articles(url: str, timeout_s: int = 20) -> list[dict]:
    with urllib.request.urlopen(url, timeout=timeout_s) as response:
        payload = response.read().decode("utf-8")
    return parse_gdelt_response(payload)


def parse_gdelt_response(text: str) -> list[dict]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    articles = payload.get("articles", [])
    if not isinstance(articles, list):
        return []
    normalized = []
    for article in articles:
        if not isinstance(article, dict):
            continue
        url = article.get("url")
        title = article.get("title")
        if not url or not title:
            continue
        normalized.append(
            {
                "url": url,
                "title": title,
                "seendate": article.get("seendate"),
                "sourcecountry": article.get("sourcecountry"),
                "domain": article.get("domain"),
            }
        )
    return normalized


_STOPWORDS = {
    "will",
    "be",
    "by",
    "the",
    "and",
    "or",
    "of",
    "a",
    "o",
    "a",
    "e",
    "de",
    "da",
    "do",
    "dos",
    "das",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "para",
    "até",
    "ate",
    "será",
    "sera",
    "serao",
    "serão",
}


def build_query(question: str, region: Optional[str], extra_query: Optional[str]) -> str:
    tokens = _extract_keywords(question)
    if tokens:
        base = " OR ".join(tokens)
        query = f"({base})"
    else:
        query = question
    if region:
        query = f"{query} AND {region}"
    if extra_query:
        query = f"{query} AND ({extra_query})"
    return query


def _extract_keywords(text: str, max_tokens: int = 6) -> list[str]:
    words = re.findall(r"[\\w\\-]{4,}", text.lower())
    tokens: list[str] = []
    for word in words:
        if word in _STOPWORDS:
            continue
        if word.isdigit():
            continue
        if word not in tokens:
            tokens.append(word)
        if len(tokens) >= max_tokens:
            break
    return tokens
