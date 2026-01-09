import argparse
from typing import Optional

from base_rate_harness.llm import AnthropicMessagesClient
from base_rate_harness.runner import run as run_outside_view
from inside_view_harness.runner import run as run_inside_view


def run(
    questions_path: str,
    mechanisms_path: str,
    evidence_path: str,
    priors_output_path: str,
    output_path: str,
    model: str,
    prompt_ids: list[str],
    temperature: float,
    discard_log_path: Optional[str] = None,
    adjustment_log_path: Optional[str] = None,
    strategy: str = "top_k",
    top_k: int = 3,
    cap_db: float = 15.0,
    source_repeat_discount: float = 0.5,
    client: Optional[AnthropicMessagesClient] = None,
) -> dict:
    outside_summary = run_outside_view(
        input_path=questions_path,
        output_path=priors_output_path,
        model=model,
        prompt_ids=prompt_ids,
        temperature=temperature,
        append=False,
        client=client,
    )
    inside_summary = run_inside_view(
        priors_path=priors_output_path,
        mechanisms_path=mechanisms_path,
        evidence_path=evidence_path,
        output_path=output_path,
        discard_log_path=discard_log_path,
        adjustment_log_path=adjustment_log_path,
        strategy=strategy,
        top_k=top_k,
        cap_db=cap_db,
        source_repeat_discount=source_repeat_discount,
    )
    return {"outside": outside_summary, "inside": inside_summary}


def main() -> None:
    parser = argparse.ArgumentParser(description="Combined outside-view and inside-view runner")
    parser.add_argument("--input", required=True)
    parser.add_argument("--mechanisms", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--priors-output", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompts", required=True)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--discard-log")
    parser.add_argument("--adjustment-log")
    parser.add_argument("--strategy", choices=["top_k", "source_discount", "cap"], default="top_k")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--cap-db", type=float, default=15.0)
    parser.add_argument("--source-repeat-discount", type=float, default=0.5)
    args = parser.parse_args()

    prompt_ids = [p.strip() for p in args.prompts.split(",") if p.strip()]
    summary = run(
        questions_path=args.input,
        mechanisms_path=args.mechanisms,
        evidence_path=args.evidence,
        priors_output_path=args.priors_output,
        output_path=args.output,
        model=args.model,
        prompt_ids=prompt_ids,
        temperature=args.temperature,
        discard_log_path=args.discard_log,
        adjustment_log_path=args.adjustment_log,
        strategy=args.strategy,
        top_k=args.top_k,
        cap_db=args.cap_db,
        source_repeat_discount=args.source_repeat_discount,
    )

    outside = summary["outside"]
    inside = summary["inside"]
    print(
        "outside_written={outside_written} outside_parse_failures={outside_parse_failures} "
        "outside_call_failures={outside_call_failures} inside_written={inside_written} "
        "inside_discards={inside_discards} inside_adjustments={inside_adjustments}".format(
            outside_written=outside["n_records_written"],
            outside_parse_failures=outside["n_parse_failures"],
            outside_call_failures=outside["n_call_failures"],
            inside_written=inside["n_records_written"],
            inside_discards=inside["n_discards"],
            inside_adjustments=inside["n_adjustments"],
        )
    )


if __name__ == "__main__":
    main()
