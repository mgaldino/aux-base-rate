import argparse
from datetime import datetime, timezone
from typing import Optional

from mechanism_harness.io import read_jsonl, write_jsonl
from mechanism_harness.llm import MechanismLLMClient, MechanismLLMConfig
from mechanism_harness.parse import parse_mechanisms_output
from mechanism_harness.prompts import SYSTEM_PROMPT, USER_PROMPT


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_optional(value: object) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str) and not value.strip():
        return "N/A"
    return str(value)


def _render_user_prompt(question: dict) -> str:
    return USER_PROMPT.format(
        question_id=_normalize_optional(question.get("question_id")),
        question=_normalize_optional(question.get("question")),
        reference_date=_normalize_optional(question.get("reference_date")),
        region=_normalize_optional(question.get("region")),
        notes=_normalize_optional(question.get("notes")),
    )


def run(
    input_path: str,
    output_path: str,
    model: str,
    temperature: float = 0.2,
    client: Optional[MechanismLLMClient] = None,
) -> dict:
    questions = read_jsonl(input_path)
    client = client or MechanismLLMClient()
    cfg = MechanismLLMConfig(model=model, temperature=temperature)

    records: list[dict] = []
    parse_failures = 0
    call_failures = 0

    for question in questions:
        qid = question.get("question_id")
        user_prompt = _render_user_prompt(question)
        text, call_error = client.generate(SYSTEM_PROMPT, user_prompt, cfg)
        mechanisms = None
        parse_error = None
        if text is not None:
            mechanisms, parse_error = parse_mechanisms_output(text)
        if call_error:
            call_failures += 1
        if parse_error:
            parse_failures += 1
        record = {
            "question_id": qid,
            "mechanisms": mechanisms or [],
            "parse_error": parse_error,
            "call_error": call_error,
            "meta": {
                "model": model,
                "temperature": temperature,
                "run_ts": _utc_timestamp(),
            },
        }
        records.append(record)

    n_written = write_jsonl(output_path, records, append=False)
    return {
        "n_questions": len(questions),
        "n_written": n_written,
        "n_parse_failures": parse_failures,
        "n_call_failures": call_failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Mechanism generation harness")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args()

    summary = run(
        input_path=args.input,
        output_path=args.output,
        model=args.model,
        temperature=args.temperature,
    )
    print(
        "n_questions={n_questions} n_written={n_written} n_parse_failures={n_parse_failures} "
        "n_call_failures={n_call_failures}".format(**summary)
    )


if __name__ == "__main__":
    main()
