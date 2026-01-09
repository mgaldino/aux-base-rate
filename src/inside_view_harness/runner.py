import argparse
import math
from datetime import datetime, timezone
from typing import Optional

from inside_view_harness.inside_view import InsideViewConfig, apply_inside_view
from inside_view_harness.io import read_jsonl, write_jsonl
from inside_view_harness.parse import normalize_evidence


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _build_mechanism_map(rows: list[dict]) -> dict[str, list[dict]]:
    mapping: dict[str, list[dict]] = {}
    for row in rows:
        qid = row.get("question_id")
        if not qid:
            continue
        mapping[qid] = row.get("mechanisms", [])
    return mapping


def run(
    priors_path: str,
    mechanisms_path: str,
    evidence_path: str,
    output_path: str,
    discard_log_path: Optional[str] = None,
    adjustment_log_path: Optional[str] = None,
    strategy: str = "top_k",
    top_k: int = 3,
    cap_db: float = 15.0,
    source_repeat_discount: float = 0.5,
) -> dict:
    prior_rows = read_jsonl(priors_path)
    mechanism_rows = read_jsonl(mechanisms_path)
    evidence_rows = read_jsonl(evidence_path)

    mechanism_map = _build_mechanism_map(mechanism_rows)
    mechanism_ids_map = {
        qid: {m.get("id") for m in mechanisms if m.get("id")}
        for qid, mechanisms in mechanism_map.items()
    }

    discards: list[dict] = []
    adjustments: list[dict] = []
    evidence_by_question: dict[str, list] = {}

    for evidence in evidence_rows:
        qid = evidence.get("question_id")
        mechanism_ids = mechanism_ids_map.get(qid, set())
        normalized, discard, adjustment_rows = normalize_evidence(evidence, mechanism_ids)
        if discard:
            discards.append(discard)
        if adjustment_rows:
            adjustments.extend(adjustment_rows)
        if normalized:
            evidence_by_question.setdefault(qid, []).append(normalized)

    cfg = InsideViewConfig(
        strategy=strategy,
        top_k=top_k,
        cap_db=cap_db,
        source_repeat_discount=source_repeat_discount,
    )

    records: list[dict] = []
    for prior_row in prior_rows:
        qid = prior_row.get("question_id")
        prompt_id = prior_row.get("prompt_id")
        base_rate = prior_row.get("base_rate")
        if base_rate is None:
            raise ValueError(f"missing base_rate for question_id={qid} prompt_id={prompt_id}")
        try:
            base_rate_value = float(base_rate)
        except (TypeError, ValueError):
            raise ValueError(
                f"invalid_base_rate for question_id={qid} prompt_id={prompt_id}"
            ) from None
        if not math.isfinite(base_rate_value) or base_rate_value <= 0 or base_rate_value >= 100:
            raise ValueError(
                f"base_rate_out_of_bounds for question_id={qid} prompt_id={prompt_id}"
            )
        prior = base_rate_value / 100.0
        mechanisms = mechanism_map.get(qid)
        if mechanisms is None:
            raise ValueError(f"missing mechanisms for question_id={qid}")
        evidence_items = evidence_by_question.get(qid, [])
        posterior, by_mechanism = apply_inside_view(prior, mechanisms, evidence_items, cfg)
        record = {
            "question_id": qid,
            "prompt_id": prompt_id,
            "prior": prior,
            "posterior": posterior,
            "by_mechanism": by_mechanism,
            "meta": {
                "run_ts": _utc_timestamp(),
                "version": "inside_view_v1",
            },
        }
        records.append(record)

    n_written = write_jsonl(output_path, records, append=False)
    n_discards = 0
    n_adjustments = 0
    if discard_log_path:
        n_discards = write_jsonl(discard_log_path, discards, append=False)
    if adjustment_log_path:
        n_adjustments = write_jsonl(adjustment_log_path, adjustments, append=False)

    return {
        "n_records_written": n_written,
        "n_discards": n_discards,
        "n_adjustments": n_adjustments,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inside-view harness")
    parser.add_argument("--priors", required=True)
    parser.add_argument("--mechanisms", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--discard-log")
    parser.add_argument("--adjustment-log")
    parser.add_argument("--strategy", choices=["top_k", "source_discount", "cap"], default="top_k")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--cap-db", type=float, default=15.0)
    parser.add_argument("--source-repeat-discount", type=float, default=0.5)
    args = parser.parse_args()

    summary = run(
        priors_path=args.priors,
        mechanisms_path=args.mechanisms,
        evidence_path=args.evidence,
        output_path=args.output,
        discard_log_path=args.discard_log,
        adjustment_log_path=args.adjustment_log,
        strategy=args.strategy,
        top_k=args.top_k,
        cap_db=args.cap_db,
        source_repeat_discount=args.source_repeat_discount,
    )

    print(
        "n_records_written={n_records_written} n_discards={n_discards} "
        "n_adjustments={n_adjustments}".format(**summary)
    )


if __name__ == "__main__":
    main()
