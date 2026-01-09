# Base Rate Harness

MVP prompt-iteration harness for outside-view base rates on binary political forecast questions.

MVP status: complete (outside-view harness, inside-view harness, combined runner).

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Python version: requires >=3.11 (tested with 3.13.3). Use `python3` from a 3.11+ install.

Environment:
```bash
python3 -V
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
All variants share the same system prompt (exact text):

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

Prompt variants (exact user prompt templates):

`v0`:

```
Question ID: {question_id}
Question: {question}
Reference date: {reference_date}
Region: {region}
Notes: {notes}

Provide the base rate as instructed.
```

`v0_1`:

```
Question ID: {question_id}
Question: {question}
Reference date: {reference_date}
Region: {region}
Notes: {notes}

Provide the base rate as instructed.
Use ONLY outside-view base rates. Do not mention polls, opponents, polarization, or “how close the race is”.
```

`v0_2`:

```
Question ID: {question_id}
Question: {question}
Reference date: {reference_date}
Region: {region}
Notes: {notes}

Provide the base rate as instructed.
If you give a precise percentage (not a wide range), you must list the specific historical cases you are counting. Otherwise, provide a wide interval (e.g., 30–70%), then average it to a single number and say why the range is wide.
```

`v0_3`:

```
Question ID: {question_id}
Question: {question}
Reference date: {reference_date}
Region: {region}
Notes: {notes}

Provide the base rate as instructed.
IMPORTANT FORMAT RULE:
- The first line must be exactly "BASE_RATE: <number>%".
- The second line must start with "RATIONALE:".
- Do not write any text before BASE_RATE.

Inside the RATIONALE only, do this:

1) TYPE (create a new event type label)
Create a short label (3–10 words) that generalizes the event into a reusable category.
It should describe WHAT happens and to WHOM/WHAT, not the specific names.
Examples of TYPE labels (examples only; create your own if needed):
- "incumbent reelected in national election"
- "electoral court declares candidate ineligible"
- "supreme court strikes down policy as unconstitutional"
- "legislation enacted by deadline"
- "targeted political violence against public figure"
- "public opinion support exceeds threshold by deadline"

2) DIMENSIONS (define what makes events 'similar')
Define the TYPE using 3–5 dimensions. Use concrete, observable dimensions like:
- actor/target role (e.g., incumbent president, candidate, court, agency, public figure)
- action/outcome (e.g., reelected, declared ineligible, ruled unconstitutional, law enacted, violence occurs)
- institution/process (e.g., election, court ruling, legislation, administrative decision, survey release)
- jurisdiction/region level (e.g., Brazil national, state, municipality)
- time structure (e.g., by a fixed deadline; open-ended; within X months)
Write dimensions as key:value pairs.

3) ANALOGS (optional, but disciplined)
List 1–3 comparable historical examples ONLY if you are confident they are real and broadly comparable.
If you are not confident, write: "ANALOGS: none (not confident)".
Do not invent examples.

4) PRIOR (base rate)
Give the outside-view base rate. If you cannot support a precise point estimate without inventing statistics, include a broad range in the rationale as:
RANGE: a-b%
and set BASE_RATE to the midpoint of that range.

Reminder:
- Do not use polls, recent news, named opponents, or any case-specific signals.
- BASE_RATE must be a single number, not a range.
```

`v0_4`:

```
Question ID: {question_id}
Question: {question}
Reference date: {reference_date}
Region: {region}
Notes: {notes}

Provide the base rate as instructed.
Be an objective Bayesian: provide an outside-view prior probability for this question, based on the historical frequency of similar events before the reference date.
Do not use case-specific signals (polls, named opponents, recent news, “current climate”).
Do not invent numeric frequencies (e.g., “3 out of 6”) unless you also name the specific cases you are counting;
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

## Inside-view (MVP)
Inside-view is a separate pipeline that reads:

- prior results JSONL (outside-view output)
- mechanisms JSONL (per question)
- evidence JSONL (per item)

It writes:

- posterior JSONL (one record per `question_id × prompt_id`)
- optional discard log JSONL
- optional adjustment log JSONL

Notes:
- `novelty_score` defaults to `1.0` when missing.
- `novelty_score` is clamped to `[0, 1]` and logged to the adjustment log when changed.
- Evidence with `evidence_db < 10`, negative `evidence_db`, or invalid direction is discarded and logged.
- Evidence with missing or non-numeric `evidence_db` is discarded and logged.
- Evidence with `evidence_db` not in {10, 20, 30, 40} is discarded and logged.
- Evidence with invalid `novelty_score` is discarded and logged.
- Evidence with missing/unknown mechanism is discarded and logged.
- `base_rate` must be strictly between 0 and 100 (exclusive).

Inside-view CLI:
```bash
inside-view-harness \
  --priors results.priors.jsonl \
  --mechanisms mechanisms.jsonl \
  --evidence evidence.jsonl \
  --output results.posterior.jsonl \
  --discard-log discarded.jsonl \
  --adjustment-log adjustments.jsonl
```

Inside-view example files:
- `examples/inside_view/priors.jsonl`
- `examples/inside_view/mechanisms.jsonl`
- `examples/inside_view/evidence.jsonl`
- `examples/inside_view/posterior.jsonl`

Real run example (BR_Q005):
- `examples/runs/br_q005/priors.br_q005.jsonl`
- `examples/runs/br_q005/mechanisms.br_q005.jsonl`
- `examples/runs/br_q005/evidence.br_q005.jsonl`
- `examples/runs/br_q005/results.priors.br_q005.jsonl`
- `examples/runs/br_q005/results.inside_view.br_q005.jsonl`
- `examples/runs/br_q005/results.combined.br_q005.jsonl`
- `examples/runs/br_q005/discarded.br_q005.jsonl`
- `examples/runs/br_q005/adjustments.br_q005.jsonl`
- `examples/runs/br_q005/discarded.combined.br_q005.jsonl`
- `examples/runs/br_q005/adjustments.combined.br_q005.jsonl`

Out of MVP (next iteration candidates):
- Evidence deduplication and novelty scoring heuristics (beyond manual `novelty_score`).
- Mechanism `prior_weight` and `confidence` usage in updates.
- Correlation A/B experiments (top-k vs source-discount) and calibration.
- Combined runner options for manual priors and resume/append runs.

## Combined runner (MVP)
Runs outside-view first and then inside-view using the outside output as priors.

```bash
combined-harness \
  --input questions.sample.jsonl \
  --mechanisms mechanisms.jsonl \
  --evidence evidence.jsonl \
  --priors-output results.priors.jsonl \
  --output results.posterior.jsonl \
  --model claude-3-5-sonnet-20240620 \
  --prompts v0 \
  --temperature 0.2 \
  --discard-log discarded.jsonl \
  --adjustment-log adjustments.jsonl
```

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
