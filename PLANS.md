# P0 Plan

## Milestone
Ship an MVP with outside-view, inside-view, and combined runners for binary political forecast questions.

## Acceptance Criteria
- Python 3.11+ project with src layout and hatchling packaging.
- JSONL input/output only; no database usage.
- Anthropic Messages API integration with retries and exponential backoff.
- Outside-view parsing uses the `BASE_RATE:` first-line convention and extracts `RATIONALE:`.
- Inside-view uses discrete `evidence_db` levels {10, 20, 30, 40} and logs discards/adjustments.
- CLI supports outside-view, inside-view, and combined runners.
- Output records remain one per `(question_id × prompt_id)`.
- Tests cover IO, prompts, parsing, runners, and inside-view edge cases.
