import argparse
from datetime import datetime, timezone
from typing import Iterable, Optional

from base_rate_harness.io import read_jsonl, write_jsonl
from base_rate_harness.llm import AnthropicMessagesClient, LLMConfig
from base_rate_harness.parse import parse_model_output
from base_rate_harness.prompts import default_registry, render_user_prompt, select_prompts


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_records(
    questions: list[dict],
    prompt_ids: list[str],
    model: str,
    temperature: float,
    client: Optional[AnthropicMessagesClient] = None,
) -> Iterable[dict]:
    registry = default_registry()
    variants = select_prompts(registry, prompt_ids)
    client = client or AnthropicMessagesClient()
    cfg = LLMConfig(model=model, temperature=temperature)

    for question in questions:
        qid = question.get("question_id")
        for variant in variants:
            user_prompt = render_user_prompt(variant, question)
            text, call_error = client.generate(variant.system, user_prompt, cfg)
            raw_response = text
            parsed = None
            parse_error = None
            base_rate = None
            if text is not None:
                parsed = parse_model_output(text)
                parse_error = parsed.parse_error
                base_rate = parsed.base_rate
            elif call_error:
                parse_error = None
            record = {
                "question_id": qid,
                "prompt_id": variant.prompt_id,
                "base_rate": base_rate,
                "prompt": {
                    "system": variant.system,
                    "user": user_prompt,
                },
                "raw_response": raw_response,
                "parse_error": parse_error,
                "call_error": call_error,
                "meta": {
                    "model": model,
                    "temperature": temperature,
                    "run_ts": _utc_timestamp(),
                },
            }
            yield record


def run(
    input_path: str,
    output_path: str,
    model: str,
    prompt_ids: list[str],
    temperature: float,
    append: bool = False,
    client: Optional[AnthropicMessagesClient] = None,
) -> dict:
    questions = read_jsonl(input_path)
    _validate_questions(questions)
    records = list(build_records(questions, prompt_ids, model, temperature, client=client))
    n_written = write_jsonl(output_path, records, append=append)
    n_parse_failures = sum(1 for r in records if r.get("parse_error"))
    n_call_failures = sum(1 for r in records if r.get("call_error"))
    summary = {
        "n_questions": len(questions),
        "n_prompts": len(prompt_ids),
        "n_records_written": n_written,
        "n_parse_failures": n_parse_failures,
        "n_call_failures": n_call_failures,
    }
    return summary


def _validate_questions(questions: list[dict]) -> None:
    for idx, question in enumerate(questions):
        question_id = question.get("question_id")
        if question_id is None or (isinstance(question_id, str) and not question_id.strip()):
            raise ValueError(f"missing question_id at index {idx}")
        question_text = question.get("question")
        if question_text is None or (isinstance(question_text, str) and not question_text.strip()):
            raise ValueError(f"missing question at index {idx}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Base rate prompt-iteration harness")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompts", required=True)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    prompt_ids = [p.strip() for p in args.prompts.split(",") if p.strip()]
    summary = run(
        input_path=args.input,
        output_path=args.output,
        model=args.model,
        prompt_ids=prompt_ids,
        temperature=args.temperature,
        append=args.append,
    )

    print(
        "n_questions={n_questions} n_prompts={n_prompts} n_records_written={n_records_written} "
        "n_parse_failures={n_parse_failures} n_call_failures={n_call_failures}".format(
            **summary
        )
    )


if __name__ == "__main__":
    main()
