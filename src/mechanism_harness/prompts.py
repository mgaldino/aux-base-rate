SYSTEM_PROMPT = """You are generating mechanisms that explain how the outcome might happen.
Return concise, reusable mechanism labels, not evidence or forecasts.
Output JSON only, no extra text."""

USER_PROMPT = """Question ID: {question_id}
Question: {question}
Reference date: {reference_date}
Region: {region}
Notes: {notes}

Return JSON with:
{{
  "mechanisms": [
    {{"id": "m1_short_slug", "label": "short mechanism label", "prior_weight": 0.33}}
  ]
}}

Rules:
- Provide 3 to 5 mechanisms.
- Each id must be unique and stable, use lowercase snake_case.
- Labels should describe a causal pathway (not evidence).
- prior_weight is optional (0-1) and does not need to sum to 1.
"""
