import argparse
import hashlib
from datetime import datetime, timezone
from typing import Optional

from evidence_harness.gdelt import build_gdelt_url, build_query, fetch_gdelt_articles
from evidence_harness.io import read_jsonl, write_jsonl
from evidence_harness.llm import EvidenceLLMClient, EvidenceLLMConfig
from evidence_harness.parse import parse_assignments_output
from evidence_harness.prompts import SYSTEM_PROMPT, USER_PROMPT
from question_io import read_questions


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_optional(value: object) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str) and not value.strip():
        return "N/A"
    return str(value)


def _article_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]


def _render_articles(articles: list[dict], max_articles: int) -> tuple[str, dict[str, dict]]:
    limited = articles[:max_articles]
    id_map: dict[str, dict] = {}
    lines = []
    for article in limited:
        url = article["url"]
        article_id = _article_id(url)
        id_map[article_id] = article
        title = article.get("title", "")
        seendate = article.get("seendate", "")
        lines.append(f"- {article_id}: {title} (seendate={seendate})")
    return "\n".join(lines), id_map


def _render_mechanisms(mechanisms: list[dict]) -> str:
    lines = []
    for mech in mechanisms:
        mech_id = mech.get("id")
        label = mech.get("label")
        if mech_id and label:
            lines.append(f"- {mech_id}: {label}")
    return "\n".join(lines)


def _render_user_prompt(question: dict, mechanisms: list[dict], articles: list[dict], max_articles: int) -> tuple[str, dict[str, dict]]:
    article_block, id_map = _render_articles(articles, max_articles)
    return (
        USER_PROMPT.format(
            question_id=_normalize_optional(question.get("question_id")),
            question=_normalize_optional(question.get("question")),
            reference_date=_normalize_optional(question.get("reference_date")),
            region=_normalize_optional(question.get("region")),
            notes=_normalize_optional(question.get("notes")),
            mechanisms=_render_mechanisms(mechanisms),
            articles=article_block or "N/A",
        ),
        id_map,
    )


def run(
    questions_path: str,
    mechanisms_path: str,
    output_path: str,
    model: str,
    temperature: float = 0.2,
    gdelt_timespan: str = "30d",
    gdelt_max_records: int = 50,
    gdelt_extra_query: Optional[str] = "politics OR election OR court OR congress OR government",
    max_articles: int = 20,
    client: Optional[EvidenceLLMClient] = None,
) -> dict:
    questions = read_questions(questions_path)
    mechanism_rows = read_jsonl(mechanisms_path)
    mechanism_map = {row.get("question_id"): row.get("mechanisms", []) for row in mechanism_rows}

    client = client or EvidenceLLMClient()
    cfg = EvidenceLLMConfig(model=model, temperature=temperature)

    records: list[dict] = []
    parse_failures = 0
    call_failures = 0

    for question in questions:
        qid = question.get("question_id")
        mechanisms = mechanism_map.get(qid, [])
        question_text = question.get("question") or ""
        region = question.get("region") or ""
        query = build_query(question_text, region, gdelt_extra_query)
        url = build_gdelt_url(query, max_records=gdelt_max_records, timespan=gdelt_timespan)
        articles = fetch_gdelt_articles(url)

        user_prompt, article_map = _render_user_prompt(question, mechanisms, articles, max_articles)
        text, call_error = client.generate(SYSTEM_PROMPT, user_prompt, cfg)
        assignments = None
        parse_error = None
        if text is not None:
            assignments, parse_error = parse_assignments_output(text)
        if call_error:
            call_failures += 1
        if parse_error:
            parse_failures += 1

        if assignments:
            for assignment in assignments:
                article_id = assignment["article_id"]
                article = article_map.get(article_id)
                if not article:
                    continue
                records.append(
                    {
                        "evidence_id": article_id,
                        "question_id": qid,
                        "mechanism_id": assignment["mechanism_id"],
                        "direction": assignment["direction"],
                        "evidence_db": assignment["evidence_db"],
                        "novelty_score": assignment.get("novelty_score", 1.0),
                        "source": "gdelt",
                        "timestamp": article.get("seendate"),
                        "url": article.get("url"),
                        "summary": article.get("title"),
                        "notes": assignment.get("notes"),
                        "meta": {
                            "gdelt_query": query,
                            "run_ts": _utc_timestamp(),
                        },
                    }
                )

    n_written = write_jsonl(output_path, records, append=False)
    return {
        "n_questions": len(questions),
        "n_written": n_written,
        "n_parse_failures": parse_failures,
        "n_call_failures": call_failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evidence generation harness (GDELT + LLM)")
    parser.add_argument("--questions", required=True)
    parser.add_argument("--mechanisms", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--gdelt-timespan", default="30d")
    parser.add_argument("--gdelt-max-records", type=int, default=50)
    parser.add_argument("--gdelt-extra-query", default="politics OR election OR court OR congress OR government")
    parser.add_argument("--max-articles", type=int, default=20)
    args = parser.parse_args()

    summary = run(
        questions_path=args.questions,
        mechanisms_path=args.mechanisms,
        output_path=args.output,
        model=args.model,
        temperature=args.temperature,
        gdelt_timespan=args.gdelt_timespan,
        gdelt_max_records=args.gdelt_max_records,
        gdelt_extra_query=args.gdelt_extra_query,
        max_articles=args.max_articles,
    )
    print(
        "n_questions={n_questions} n_written={n_written} n_parse_failures={n_parse_failures} "
        "n_call_failures={n_call_failures}".format(**summary)
    )


if __name__ == "__main__":
    main()
