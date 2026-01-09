# P0 Plan

## Milestone
Ship an MVP prompt-iteration harness for outside-view base rates on binary political forecast questions.

## Acceptance Criteria
- Python 3.11 project with src layout and hatchling packaging.
- JSONL input/output only; no database usage.
- Anthropic Messages API integration with retries and exponential backoff.
- Output parsing uses the `BASE_RATE:` first-line convention and extracts `RATIONALE:`.
- CLI supports prompt variants and emits one record per question × prompt.
- Tests cover IO, prompts, parsing, and runner with a fake client.
