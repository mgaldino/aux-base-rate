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

## Prompts
All variants share the same system prompt:

```
You are estimating an OUTSIDE-VIEW base rate only; later I will combine this base rate with case-specific signals. Your job is to provide the outside-view prior.
Use only historical regularities that would be available before the reference date provided by the user.
Do not use polls, “current climate”, named opponents, campaign facts, or any case-specific signals.
Do not claim specific historical frequencies (e.g., “3 of 6”) unless you can name the concrete cases you are counting.
BASE_RATE must be a single number (not a range). If uncertain, put the range in the RATIONALE as "RANGE: a–b%" and set BASE_RATE to the midpoint.
Output must follow exactly:
BASE_RATE: <0–100>%
RATIONALE: <short text including, if needed, a plausible range and why>
```

Prompt variants:

- `v0`: base prompt only.
- `v0_1`: outside-view only; do not mention polls/opponents/polarization/“how close the race is”.
- `v0_2`: if precise, list concrete cases; otherwise use a wide interval, average it, and explain the range.
- `v0_3`: structured rationale (TYPE, DIMENSIONS, ANALOGS, PRIOR) with strict formatting rules.
- `v0_4`: objective Bayesian prior with historical frequency, no case-specific signals.

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

If your source JSON uses different keys (e.g., `id`, `title`, `description`), map them into the schema above.

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

## Example (BR_Q005)
Input JSON (source):

```json
{"id":"BR_Q005","title":"O TSE declarará Jair Bolsonaro inelegível (caso da reunião com embaixadores) até 15/07/2023?","description":"Pergunta retro: inelegibilidade por 8 anos contados a partir das Eleições 2022, no caso da reunião com embaixadores e uso indevido de meios de comunicação.","resolution_criteria":"Resolver SIM se o TSE publicar decisão/nota oficial declarando Bolsonaro inelegível nesse caso até 15/07/2023 (inclusive). Caso contrário, NÃO.","close_time":"2023-06-29T23:59:00-03:00","resolve_time":"2023-06-30T20:30:00-03:00"}
```

Mapped JSONL line:

```json
{"question_id":"BR_Q005","question":"O TSE declarará Jair Bolsonaro inelegível (caso da reunião com embaixadores) até 15/07/2023?","reference_date":"2023-07-15","region":"Brasil","notes":"Pergunta retro: inelegibilidade por 8 anos contados a partir das Eleições 2022, no caso da reunião com embaixadores e uso indevido de meios de comunicação. Resolver SIM se o TSE publicar decisão/nota oficial declarando Bolsonaro inelegível nesse caso até 15/07/2023 (inclusive). Caso contrário, NÃO."}
```

CLI:

```bash
python -m base_rate_harness.runner \
  --input questions.br_q005.jsonl \
  --output results.br_q005.jsonl \
  --model claude-3-haiku-20240307 \
  --prompts v0,v0_1,v0_2,v0_3,v0_4 \
  --temperature 0.2
```

Example output record (format only):

```json
{"question_id":"BR_Q005","prompt_id":"v0","base_rate":30.0,"prompt":{"system":"...","user":"..."},"raw_response":"BASE_RATE: 30%\nRATIONALE: RANGE: 20–40% ...","parse_error":null,"call_error":null,"meta":{"model":"claude-3-haiku-20240307","temperature":0.2,"run_ts":"2025-01-01T00:00:00Z"}}
```
