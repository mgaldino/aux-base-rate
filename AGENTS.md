# Agent Rules

- Test-first: add or update tests before implementing behavior.
- Modularity: keep `io`, `prompts`, `llm`, `parse`, `runner` as separate modules.
- Reproducible runs: inputs/outputs must be file-based JSONL; no DB.
- Output records: one record per `(question_id × prompt_id)`.
