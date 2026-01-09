# Inside View Plan (Draft)

This document defines a minimal, testable inside-view pipeline that can be
implemented in steps.

## Goals (P0)
- Accept manual evidence as JSONL.
- Define 3–5 mechanisms per question.
- Update the outside-view base rate using discrete dB evidence with
  correlation control by mechanism.
- Avoid narrative fallacy and double counting.

## Evidence Scale (dB)
- 10 dB: weak (minimum usable; below 10 dB discard)
- 20 dB: moderate
- 30 dB: strong
- 40 dB: very strong (ceiling)

## Guardrails
- Every evidence item must map to exactly one mechanism.
- Evidence within the same mechanism is correlated.
- Deduplicate near-duplicate items; reduce weight for low novelty.
- No case-specific narrative without a mechanism + observable signal.

## Data Schemas (JSONL)

Question mechanisms (one line per question):
```json
{
  "question_id": "BR_Q005",
  "mechanisms": [
    {"id": "m1_tse_balance", "label": "equilibrio politico no TSE", "prior_weight": 0.35},
    {"id": "m2_speed", "label": "capacidade do TSE de julgar rapido", "prior_weight": 0.25},
    {"id": "m3_quality", "label": "qualidade da acusacao", "prior_weight": 0.40}
  ]
}
```

Evidence items (one line per item):
```json
{
  "evidence_id": "ev_2023_06_20_001",
  "question_id": "BR_Q005",
  "timestamp": "2023-06-20T12:00:00Z",
  "source": "news",
  "url": "https://...",
  "summary": "Noticia X coloca em duvida a reuniao com embaixadores",
  "mechanism_id": "m3_quality",
  "direction": "NO",
  "evidence_db": 10,
  "novelty_score": 0.8,
  "confidence": "medium",
  "notes": "Evidencia direta sobre fragilidade da acusacao"
}
```

## Update Rule (dB)

Let `p` be the outside-view base rate (prior).

For each mechanism `m`:
1) Collect evidence items `i` mapped to `m`.
2) Compute effective dB using correlation control:
   - `raw_db = sum(evidence_db_i * novelty_score_i * direction_sign)`
   - `corr_discount = 1 / sqrt(n_items_m)` (or `1 / (1 + 0.3*(n-1))`)
   - `effective_db_m = raw_db * corr_discount`

Total update:
```
logit(posterior) = logit(prior) + sum(effective_db_m) * ln(10) / 10
```

## Implementation Steps
1) Add `inside_view.py` with a pure function:
   - `apply_inside_view(prior, mechanisms, evidence_items) -> posterior`
2) Add input files:
   - `mechanisms.jsonl`
   - `evidence.jsonl`
3) Add tests for:
   - dB scale handling and discard rule (<10 dB)
   - mechanism correlation discount
   - direction handling (SIM/NO)
4) Integrate into `runner.py` (optional, after tests).
