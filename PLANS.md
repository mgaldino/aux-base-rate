# P0 Plan (Updated for New Phase)

## Milestone
Ship the next-phase MVP with stronger reproducibility, stricter contracts, and test-first coverage for outside-view, inside-view, and combined runners.

## Acceptance Criteria
- Python 3.11+ project with src layout and hatchling packaging.
- JSONL input/output only; no database usage; all runs are reproducible from files.
- Anthropic Messages API integration with retries and exponential backoff.
- Outside-view parsing uses the `BASE_RATE:` first-line convention and extracts `RATIONALE:`.
- Inside-view enforces discrete `evidence_db` levels {10, 20, 30, 40} and logs discards/adjustments.
- CLI supports outside-view, inside-view, and combined runners.
- Output records remain one per `(question_id × prompt_id)`.
- Tests cover io, prompts, parsing, runners, and inside-view edge cases (test-first).

## Next-Phase MVP Plan
1) Contracts and schemas (lock down)
   - Freeze JSONL schemas for priors, mechanisms, evidence, and outputs.
   - Define default correlation policy: top-k per mechanism (k=3).
   - Finalize enums/normalization rules (direction, discrete dB, novelty clamp).
   - Document all required/optional fields and defaults.
   - Deliverables checklist:
     - [ ] Schema definitions finalized (inputs/outputs).
     - [ ] Defaults and normalization rules documented.
2) Prompt + parsing consistency
   - Ensure inside-view prompt explicitly maps evidence strength to discrete `evidence_db`.
   - Add 1-2 short examples (weak vs strong) aligned with parser expectations.
   - Validate parser behavior against malformed outputs and missing fields.
   - Deliverables checklist:
     - [ ] Inside-view prompt updated with discrete mapping.
     - [ ] Example snippets added.
     - [ ] Parser expectations documented.
3) Tests (test-first)
   - IO validation: required keys, missing optional fields, JSONL line errors.
   - Parse validation: direction normalization, invalid dB, novelty out of range, unknown mechanism_id.
   - Correlation: top-k enforcement per mechanism and logging.
   - Math: logit aggregation and posterior computation per mechanism.
   - Runner: end-to-end outside-view, inside-view, combined; one record per `(question_id × prompt_id)`.
   - Deliverables checklist:
     - [ ] Unit tests for IO and parsing edge cases.
     - [ ] Tests for correlation and log handling.
     - [ ] End-to-end runner tests.
4) Modular implementation
   - Keep modules separate: `io`, `prompts`, `llm`, `parse`, `runner`.
   - Ensure inside-view logic is isolated and reusable by combined runner.
   - Add clear error handling and discard/adjustment logs in one place.
   - Deliverables checklist:
     - [ ] Module boundaries enforced in code layout.
     - [ ] Centralized logging for discards/adjustments.
5) Reproducible runs + docs
   - Standardize input/output file naming conventions in `examples/`.
   - Update `README.md` and `INSIDE_VIEW.md` with the final schema and CLI flags.
   - Add a minimal "golden run" example that can be re-run deterministically.
   - Deliverables checklist:
     - [ ] Example file naming conventions documented.
     - [ ] Docs updated with final schemas and CLI usage.
     - [ ] Golden run example added.
