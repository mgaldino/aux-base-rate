# Base Rate Harness

MVP prompt-iteration harness for outside-view base rates on binary political forecast questions.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Set your API key:

```bash
export ANTHROPIC_API_KEY=... 
```

## Run

```bash
python -m base_rate_harness.runner \
  --input questions.sample.jsonl \
  --output results.jsonl \
  --model claude-3-5-sonnet-20240620 \
  --prompts v0,v0_2 \
  --temperature 0.2
```

## Input schema (JSONL)
Each line is a JSON object:

```json
{
  "question_id": "q1",
  "question": "Will X happen by date Y?",
  "reference_date": "2025-01-01",
  "region": "Global",
  "notes": "Optional context"
}
```

Only `question_id` and `question` are required; missing optional fields are treated as `N/A` in prompts.

## Output schema (JSONL)
One record per `(question_id × prompt_id)`:

```json
{
  "question_id": "q1",
  "prompt_id": "v0",
  "base_rate": 35.0,
  "prompt": {
    "system": "...",
    "user": "..."
  },
  "raw_response": "BASE_RATE: 35%\nRATIONALE: ...",
  "parse_error": null,
  "call_error": null,
  "meta": {
    "model": "claude-3-5-sonnet-20240620",
    "temperature": 0.2,
    "run_ts": "2025-01-01T00:00:00Z"
  }
}
```

## Output convention (MVP)
The model must output:

- First line exactly: `BASE_RATE: <0-100>%` (single number, not a range)
- Second line starts with `RATIONALE: ...`
- If uncertain, include `RANGE: a–b%` inside the rationale and set `BASE_RATE` to the midpoint

Parsing only checks the first line for the base rate.
