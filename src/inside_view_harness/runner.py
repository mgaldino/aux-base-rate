import argparse
import math
from datetime import datetime, timezone
from typing import Optional

from inside_view_harness.inside_view import InsideViewConfig, apply_inside_view
from inside_view_harness.io import read_jsonl, write_jsonl
from inside_view_harness.parse import normalize_evidence
from schema_validation import validate_rows


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _resolve_run_ts(run_ts: Optional[str]) -> str:
    return run_ts or _utc_timestamp()


def _normalize_question_id(value: object, context: str) -> str:
    if value is None:
        raise ValueError(f"missing question_id in {context}")
    text = str(value).strip()
    if not text:
        raise ValueError(f"missing question_id in {context}")
    return text.casefold()


def _normalize_question_id_optional(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.casefold()


def _build_mechanism_map(rows: list[dict]) -> dict[str, list[dict]]:
    mapping: dict[str, list[dict]] = {}
    seen: dict[str, str] = {}
    for idx, row in enumerate(rows):
        qid = row.get("question_id")
        normalized_qid = _normalize_question_id(qid, f"mechanisms row {idx}")
        mechanisms = row.get("mechanisms")
        if mechanisms is None:
            raise ValueError(f"missing mechanisms for question_id={qid}")
        if not isinstance(mechanisms, list):
            raise ValueError(f"invalid mechanisms for question_id={qid}")
        for mechanism in mechanisms:
            mechanism_id = mechanism.get("id") if isinstance(mechanism, dict) else None
            if mechanism_id is None or (
                isinstance(mechanism_id, str) and not mechanism_id.strip()
            ):
                raise ValueError(f"missing mechanism id for question_id={qid}")
        if normalized_qid in seen and seen[normalized_qid] != qid:
            raise ValueError(
                "question_id collision: {a} vs {b}".format(a=seen[normalized_qid], b=qid)
            )
        seen[normalized_qid] = str(qid)
        mapping[normalized_qid] = mechanisms
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
    run_ts: Optional[str] = None,
    validate_schemas: bool = False,
    schemas_dir: Optional[str] = None,
) -> dict:
    prior_rows = read_jsonl(priors_path)
    mechanism_rows = read_jsonl(mechanisms_path)
    evidence_rows = read_jsonl(evidence_path)
    if validate_schemas:
        validate_rows(prior_rows, "priors.schema.json", schemas_dir=schemas_dir)
        validate_rows(mechanism_rows, "mechanisms.schema.json", schemas_dir=schemas_dir)
        validate_rows(evidence_rows, "evidence.schema.json", schemas_dir=schemas_dir)

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
        normalized_qid = _normalize_question_id_optional(qid)
        mechanism_ids = mechanism_ids_map.get(normalized_qid, set())
        normalized, discard, adjustment_rows = normalize_evidence(evidence, mechanism_ids)
        if discard:
            discards.append(discard)
        if adjustment_rows:
            adjustments.extend(adjustment_rows)
        if normalized:
            evidence_by_question.setdefault(normalized_qid or "", []).append(normalized)

    cfg = InsideViewConfig(
        strategy=strategy,
        top_k=top_k,
        cap_db=cap_db,
        source_repeat_discount=source_repeat_discount,
    )

    records: list[dict] = []
    resolved_run_ts = _resolve_run_ts(run_ts)
    seen_priors: dict[str, str] = {}
    for prior_row in prior_rows:
        qid = prior_row.get("question_id")
        normalized_qid = _normalize_question_id(qid, "priors")
        if normalized_qid in seen_priors and seen_priors[normalized_qid] != qid:
            raise ValueError(
                "question_id collision: {a} vs {b}".format(a=seen_priors[normalized_qid], b=qid)
            )
        seen_priors[normalized_qid] = str(qid)
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
        mechanisms = mechanism_map.get(normalized_qid)
        if mechanisms is None:
            raise ValueError(f"missing mechanisms for question_id={qid}")
        evidence_items = evidence_by_question.get(normalized_qid, [])
        posterior, by_mechanism = apply_inside_view(prior, mechanisms, evidence_items, cfg)
        record = {
            "question_id": qid,
            "prompt_id": prompt_id,
            "prior": prior,
            "posterior": posterior,
            "by_mechanism": by_mechanism,
            "meta": {
                "run_ts": resolved_run_ts,
                "version": "inside_view_v1",
            },
        }
        records.append(record)

    if validate_schemas:
        validate_rows(records, "inside_view_output.schema.json", schemas_dir=schemas_dir)
        if discards:
            validate_rows(discards, "discard_log.schema.json", schemas_dir=schemas_dir)
        if adjustments:
            validate_rows(adjustments, "adjustment_log.schema.json", schemas_dir=schemas_dir)

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
    parser.add_argument("--run-ts", help="Override run timestamp (ISO-8601)")
    parser.add_argument("--validate-schemas", action="store_true")
    parser.add_argument("--schemas-dir")
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
        run_ts=args.run_ts,
        validate_schemas=args.validate_schemas,
        schemas_dir=args.schemas_dir,
    )

    print(
        "n_records_written={n_records_written} n_discards={n_discards} "
        "n_adjustments={n_adjustments}".format(**summary)
    )


if __name__ == "__main__":
    main()
