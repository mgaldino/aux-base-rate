# Workflow de Trabalho (Notas de Pesquisa)

Documento curto para registrar o fluxo utilizado na elaboracao do plano do MVP
inside-view e na checagem de consistencia de documentos.

## Objetivo
Documentar um workflow repetivel para:
- revisar documentos de referencia,
- identificar divergencias,
- fazer perguntas de esclarecimento,
- produzir um plano de MVP,
- registrar o plano no repositorio.

## Etapas do workflow
1) **Leitura inicial**
   - Ler `INSIDE_VIEW.md` para requisitos e guardrails.
   - Ler `README.md` para schema, CLI e exemplos.
   - Confirmar o ambiente local (`.venv/bin/python -V`) antes de rodar testes.
2) **Perguntas de esclarecimento**
   - Confirmar escopo (MVP end-to-end vs parcial).
   - Confirmar decisoes pendentes (ex.: correlacao default).
   - Definir fontes de verdade para schema e exemplos.
3) **Checagem de consistencia**
   - Procurar divergencias entre docs e exemplos (ex.: direcao).
   - Registrar discrepancias e confirmar correcoes.
4) **Brainstorm do plano**
   - Propor backlog minimo para end-to-end.
   - Incluir revisao de prompts (inside-view).
   - Manter modularidade e test-first.
5) **Plano formal**
   - Converter brainstorm em checkpoints/etapas.
   - Registrar em `PLANS.md`.

## Artefatos de referencia
- `INSIDE_VIEW.md`
- `README.md`
- `examples/inside_view/*`
- `PLANS.md`

## Regras aplicadas
- Test-first: testes antes de implementacao.
- Modularidade: `io`, `parse`, `runner`, `llm`, `prompts` separados.
- Reprodutibilidade: entrada/saida em JSONL, sem DB.
- Saida: um registro por `(question_id x prompt_id)`.
- Ambiente: usar `.venv/bin/python` (Python 3.13.3 testado) e nao assumir `python` fora do venv.
