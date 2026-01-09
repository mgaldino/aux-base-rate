from __future__ import annotations

import argparse
import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from base_rate_harness.io import read_jsonl


_OUTCOME_MAP = {
    "YES": 1.0,
    "Y": 1.0,
    "TRUE": 1.0,
    "SIM": 1.0,
    "NO": 0.0,
    "N": 0.0,
    "FALSE": 0.0,
    "NAO": 0.0,
    "NÃO": 0.0,
}


@dataclass(frozen=True)
class Report:
    outside: dict
    inside: dict
    brier: Optional[dict]
    details: list[dict]


def _normalize_outcome(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    text = str(value).strip()
    if not text:
        return None
    return _OUTCOME_MAP.get(text.upper())


def _load_outcomes(path: Path) -> dict[str, float]:
    outcomes: dict[str, float] = {}
    for row in read_jsonl(path):
        qid = row.get("question_id")
        normalized = _normalize_outcome(row.get("outcome"))
        if qid and normalized is not None:
            outcomes[str(qid)] = normalized
    return outcomes


def _load_questions(path: Path) -> dict[str, dict]:
    questions: dict[str, dict] = {}
    for row in read_jsonl(path):
        qid = row.get("question_id")
        if qid:
            questions[str(qid)] = row
    return questions


def _load_mechanisms(path: Optional[Path]) -> dict[str, list[dict]]:
    if not path:
        return {}
    mapping: dict[str, list[dict]] = {}
    for row in read_jsonl(path):
        qid = row.get("question_id")
        mechanisms = row.get("mechanisms") if isinstance(row.get("mechanisms"), list) else []
        if qid:
            mapping[str(qid)] = mechanisms
    return mapping


def _load_evidence(path: Optional[Path]) -> dict[str, list[dict]]:
    if not path:
        return {}
    mapping: dict[str, list[dict]] = {}
    for row in read_jsonl(path):
        qid = row.get("question_id")
        if qid:
            mapping.setdefault(str(qid), []).append(row)
    return mapping


def _collect_outside(rows: Iterable[dict]) -> dict:
    rows_list = list(rows)
    base_rates = [r.get("base_rate") for r in rows_list if r.get("base_rate") is not None]
    parse_failures = sum(1 for r in rows_list if r.get("parse_error"))
    call_failures = sum(1 for r in rows_list if r.get("call_error"))
    prompt_ids = sorted({r.get("prompt_id") for r in rows_list if r.get("prompt_id")})
    return {
        "count": len(rows_list),
        "base_rate_mean": _mean(base_rates),
        "base_rate_min": min(base_rates) if base_rates else None,
        "base_rate_max": max(base_rates) if base_rates else None,
        "parse_failures": parse_failures,
        "call_failures": call_failures,
        "prompt_ids": prompt_ids,
    }


def _collect_inside(rows: Iterable[dict]) -> dict:
    rows_list = list(rows)
    priors = [r.get("prior") for r in rows_list if r.get("prior") is not None]
    posteriors = [r.get("posterior") for r in rows_list if r.get("posterior") is not None]
    deltas = [
        (r.get("posterior") - r.get("prior"))
        for r in rows_list
        if r.get("posterior") is not None and r.get("prior") is not None
    ]
    prompt_ids = sorted({r.get("prompt_id") for r in rows_list if r.get("prompt_id")})
    return {
        "count": len(rows_list),
        "prior_mean": _mean(priors),
        "posterior_mean": _mean(posteriors),
        "delta_mean": _mean(deltas),
        "prior_min": min(priors) if priors else None,
        "prior_max": max(priors) if priors else None,
        "posterior_min": min(posteriors) if posteriors else None,
        "posterior_max": max(posteriors) if posteriors else None,
        "prompt_ids": prompt_ids,
    }


def _brier_scores(
    rows: Iterable[dict], outcomes: dict[str, float], field: str, scale: float = 1.0
) -> dict:
    scores: list[float] = []
    by_prompt: dict[str, list[float]] = {}
    for row in rows:
        qid = row.get("question_id")
        if not qid or qid not in outcomes:
            continue
        value = row.get(field)
        if value is None:
            continue
        p = float(value) * scale
        y = outcomes[qid]
        score = (p - y) ** 2
        scores.append(score)
        prompt_id = row.get("prompt_id") or "unknown"
        by_prompt.setdefault(prompt_id, []).append(score)
    return {
        "overall": _mean(scores),
        "by_prompt": {k: _mean(v) for k, v in sorted(by_prompt.items())},
    }


def build_report(
    outside_paths: list[Path],
    inside_paths: list[Path],
    questions_path: Optional[Path],
    mechanisms_path: Optional[Path] = None,
    evidence_path: Optional[Path] = None,
) -> Report:
    outside_rows: list[dict] = []
    for path in outside_paths:
        outside_rows.extend(read_jsonl(path))

    inside_rows: list[dict] = []
    for path in inside_paths:
        inside_rows.extend(read_jsonl(path))

    outside_metrics = _collect_outside(outside_rows)
    inside_metrics = _collect_inside(inside_rows)

    brier = None
    details: list[dict] = []
    if questions_path:
        outcomes = _load_outcomes(questions_path)
        if outcomes:
            brier = {
                "outside": _brier_scores(outside_rows, outcomes, "base_rate", scale=0.01),
                "inside": _brier_scores(inside_rows, outcomes, "posterior", scale=1.0),
            }
        questions = _load_questions(questions_path)
        mechanisms = _load_mechanisms(mechanisms_path)
        evidence = _load_evidence(evidence_path)
        for qid, question in questions.items():
            mech_list = mechanisms.get(qid, [])
            ev_list = evidence.get(qid, [])
            details.append(
                {
                    "question_id": qid,
                    "question": question.get("question"),
                    "mechanisms": mech_list,
                    "evidence": ev_list,
                }
            )
    return Report(outside=outside_metrics, inside=inside_metrics, brier=brier, details=details)


def render_html(report: Report) -> str:
    def fmt(value: Optional[float]) -> str:
        if value is None:
            return "-"
        return "{:.4f}".format(value)

    def fmt_percent(value: Optional[float]) -> str:
        if value is None:
            return "-"
        return "{:.2f}%".format(value)

    outside = report.outside
    inside = report.inside

    parts = [
        "<!doctype html>",
        "<html>",
        "<head>",
        "<meta charset=\"utf-8\"/>",
        "<title>Model Performance Report</title>",
        "<style>",
        "body{font-family:Arial,Helvetica,sans-serif;margin:32px;color:#111;}",
        "h1{margin-bottom:8px;}",
        "table{border-collapse:collapse;width:100%;margin:12px 0;}",
        "th,td{border:1px solid #ddd;padding:8px;text-align:left;}",
        "th{background:#f3f3f3;}",
        ".section{margin-top:24px;}",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Model Performance Report</h1>",
        "<div class=\"section\">",
        "<h2>Outside-view</h2>",
        "<table>",
        "<tr><th>Metric</th><th>Value</th></tr>",
        "<tr><td>Records</td><td>{}</td></tr>".format(outside["count"]),
        "<tr><td>Base rate mean</td><td>{}</td></tr>".format(
            fmt_percent(outside["base_rate_mean"])
        ),
        "<tr><td>Base rate min</td><td>{}</td></tr>".format(
            fmt_percent(outside["base_rate_min"])
        ),
        "<tr><td>Base rate max</td><td>{}</td></tr>".format(
            fmt_percent(outside["base_rate_max"])
        ),
        "<tr><td>Parse failures</td><td>{}</td></tr>".format(outside["parse_failures"]),
        "<tr><td>Call failures</td><td>{}</td></tr>".format(outside["call_failures"]),
        "</table>",
        "</div>",
        "<div class=\"section\">",
        "<h2>Inside-view</h2>",
        "<table>",
        "<tr><th>Metric</th><th>Value</th></tr>",
        "<tr><td>Records</td><td>{}</td></tr>".format(inside["count"]),
        "<tr><td>Prior mean</td><td>{}</td></tr>".format(fmt(inside["prior_mean"])),
        "<tr><td>Posterior mean</td><td>{}</td></tr>".format(fmt(inside["posterior_mean"])),
        "<tr><td>Mean delta</td><td>{}</td></tr>".format(fmt(inside["delta_mean"])),
        "<tr><td>Prior min</td><td>{}</td></tr>".format(fmt(inside["prior_min"])),
        "<tr><td>Prior max</td><td>{}</td></tr>".format(fmt(inside["prior_max"])),
        "<tr><td>Posterior min</td><td>{}</td></tr>".format(fmt(inside["posterior_min"])),
        "<tr><td>Posterior max</td><td>{}</td></tr>".format(fmt(inside["posterior_max"])),
        "</table>",
        "</div>",
    ]

    if report.brier:
        outside_brier = report.brier["outside"]
        inside_brier = report.brier["inside"]
        parts.extend(
            [
                "<div class=\"section\">",
                "<h2>Brier Scores</h2>",
                "<table>",
                "<tr><th>Scope</th><th>Overall</th></tr>",
                "<tr><td>Outside-view</td><td>{}</td></tr>".format(
                    fmt(outside_brier["overall"])
                ),
                "<tr><td>Inside-view</td><td>{}</td></tr>".format(
                    fmt(inside_brier["overall"])
                ),
                "</table>",
                "</div>",
            ]
        )

    if report.details:
        parts.extend(
            [
                "<div class=\"section\">",
                "<h2>Question Details</h2>",
            ]
        )
        for item in report.details:
            question_text = item.get("question") or "-"
            qid = item.get("question_id") or "-"
            parts.append("<h3>{}</h3>".format(html.escape(f"{qid}: {question_text}")))
            mechanisms = item.get("mechanisms", [])
            evidence = item.get("evidence", [])
            parts.append("<strong>Mechanisms</strong>")
            parts.append("<ul>")
            for mech in mechanisms:
                label = mech.get("label") or "-"
                mech_id = mech.get("id") or "-"
                parts.append("<li>{}</li>".format(html.escape(f"{mech_id}: {label}")))
            if not mechanisms:
                parts.append("<li>-</li>")
            parts.append("</ul>")

            parts.append("<strong>Evidence</strong>")
            if evidence:
                parts.append("<ul>")
                for ev in evidence:
                    summary = ev.get("summary") or ev.get("notes") or "-"
                    mech_id = ev.get("mechanism_id") or "-"
                    direction = ev.get("direction") or "-"
                    db = ev.get("evidence_db")
                    parts.append(
                        "<li>{}</li>".format(
                            html.escape(f"{mech_id} {direction} db={db}: {summary}")
                        )
                    )
                parts.append("</ul>")
            else:
                parts.append("<div>-</div>")
        parts.append("</div>")

    parts.extend(["</body>", "</html>"])
    return "\n".join(parts)


def _mean(values: Iterable[float]) -> Optional[float]:
    items = [float(v) for v in values]
    if not items:
        return None
    return sum(items) / len(items)


def _split_paths(value: Optional[str]) -> list[Path]:
    if not value:
        return []
    return [Path(part.strip()) for part in value.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a static HTML report from JSONL.")
    parser.add_argument("--outside", help="Outside-view results JSONL (comma-separated)")
    parser.add_argument("--inside", help="Inside-view results JSONL (comma-separated)")
    parser.add_argument("--questions", help="Questions JSONL with outcome field")
    parser.add_argument("--mechanisms", help="Mechanisms JSONL")
    parser.add_argument("--evidence", help="Evidence JSONL")
    parser.add_argument("--output", required=True, help="Output HTML path")
    args = parser.parse_args()

    outside_paths = _split_paths(args.outside)
    inside_paths = _split_paths(args.inside)
    questions_path = Path(args.questions) if args.questions else None

    mechanisms_path = Path(args.mechanisms) if args.mechanisms else None
    evidence_path = Path(args.evidence) if args.evidence else None

    report = build_report(
        outside_paths,
        inside_paths,
        questions_path,
        mechanisms_path=mechanisms_path,
        evidence_path=evidence_path,
    )
    html_text = render_html(report)
    Path(args.output).write_text(html_text, encoding="utf-8")


if __name__ == "__main__":
    main()
