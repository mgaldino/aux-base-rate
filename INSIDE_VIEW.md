# Inside View Plan (Draft)

Plano de funcionalidade inside-view com foco em modularidade, testes e
execucao reprodutivel via arquivos JSONL.

## Goals (P0)
- Aceitar evidencias manuais em JSONL (entrada e saida).
- Definir 3-5 mecanismos por pergunta.
- Atualizar o outside-view com evidencias em dB, com controle de correlacao
  dentro de cada mecanismo.
- Evitar narrativa e dupla contagem.
- Um registro de saida por (question_id x prompt_id).
- Pipeline separado do outside-view (CLI/runner proprio) usando JSONL.

## Evidence Scale (dB)
- 10 dB: fraca (minimo aceitavel; abaixo de 10 descartar)
- 20 dB: moderada
- 30 dB: forte
- 40 dB: muito forte (teto)

## Guardrails
- Cada evidencia mapeia para exatamente um mecanismo.
- Evidencias no mesmo mecanismo sao correlacionadas.
- Deduplicar evidencias quase identicas; reduzir peso por baixa novidade.
- Sem narrativa especifica sem mecanismo + sinal observavel.
- Evidencias com `evidence_db` negativo devem ser descartadas e logadas.
- Direcao invalida deve ser descartada e logada.

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

Discard log (one line per discarded item):
```json
{
  "evidence_id": "ev_2023_06_20_001",
  "question_id": "BR_Q005",
  "mechanism_id": "m3_quality",
  "reason": "db_below_threshold",
  "raw_direction": "SIM",
  "evidence_db": 5,
  "novelty_score": 0.8,
  "source": "news",
  "timestamp": "2023-06-20T12:00:00Z",
  "notes": "Evidencia abaixo do minimo"
}
```

Discard reasons (enum, MVP):
- `db_below_threshold`
- `db_negative`
- `invalid_direction`
- `missing_direction`
- `missing_mechanism`

Adjustment log (optional, non-discard; separate JSONL file):
- `novelty_clamped`

Adjustment log (one line per adjustment):
```json
{
  "evidence_id": "ev_2023_06_20_001",
  "question_id": "BR_Q005",
  "mechanism_id": "m3_quality",
  "reason": "novelty_clamped",
  "raw_novelty_score": 1.2,
  "novelty_score": 1.0,
  "source": "news",
  "timestamp": "2023-06-20T12:00:00Z",
  "notes": "Ajuste para limite superior"
}
```

Output record (one line per (question_id x prompt_id)):
```json
{
  "question_id": "BR_Q005",
  "prompt_id": "v0",
  "prior": 0.30,
  "posterior": 0.24,
  "by_mechanism": [
    {"mechanism_id": "m3_quality", "raw_db": -8.0, "effective_db": -6.5}
  ],
  "meta": {
    "run_ts": "2025-01-01T00:00:00Z",
    "version": "inside_view_v1"
  }
}
```

## Update Rule (dB)

Let `p` be the outside-view base rate (prior).

For each mechanism `m`:
1) Collect evidence items `i` mapped to `m`.
2) Normalize and validate evidence:
   - `novelty_score` default = 1.0 se ausente
   - clamp `novelty_score` para [0, 1] (logar se ajustado)
   - descartar `evidence_db` < 10 (logar)
   - descartar `evidence_db` negativo (logar)
   - descartar direcao invalida (logar)
3) Compute effective dB using correlation control (MVP):
   - Opcoes principais a testar:
     a) Top-k por mecanismo (pelo maior `evidence_db * novelty_score`; k=3)
     b) Desconto por fonte (reduzir peso para `source` repetido)
   - Fallback:
     c) Cap por mecanismo (limitar `effective_db_m` a ±15 dB)
   - Uma unica opcao deve ser default no MVP, mantendo as outras como alternativa
     documentada.
   - `raw_db = sum(evidence_db_i * novelty_score_i * direction_sign)`
   - `effective_db_m = raw_db` apos aplicar a estrategia escolhida

Total update:
```
logit(posterior) = logit(prior) + sum(effective_db_m) * ln(10) / 10
```

Direction handling:
- "SIM" => +1
- "NAO"/"NO" => -1

## Implementation Steps (test-first)
1) Tests:
   - descarte de evidencias < 10 dB
   - descarte de evidencias com `evidence_db` negativo
   - direcao SIM/NAO
   - controle de correlacao (top-k e desconto por fonte; cap como fallback)
   - log de descartes (motivos esperados)
   - agregacao por mecanismo e soma no logit
2) Modulos (separados):
   - `io.py`: leitura/escrita JSONL (mechanisms/evidence/output)
   - `parse.py`: validacao e normalizacao (direcao, dB, novelty)
   - `runner.py`: orquestracao do pipeline inside-view
3) Logica pura:
   - `inside_view.py` com `apply_inside_view(prior, mechanisms, evidence_items)`
4) Integracao opcional:
   - CLI/runner principal so apos testes passarem
