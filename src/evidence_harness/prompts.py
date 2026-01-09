SYSTEM_PROMPT = """You map news articles to mechanisms and assign evidence strength.
Output JSON only, no extra text."""

USER_PROMPT = """Question ID: {question_id}
Question: {question}
Reference date: {reference_date}
Region: {region}
Notes: {notes}

Mechanisms:
{mechanisms}

Articles:
{articles}

Return JSON with:
{{
  "assignments": [
    {{
      "article_id": "a1",
      "mechanism_id": "m1_quality",
      "direction": "YES",
      "evidence_db": 20,
      "novelty_score": 0.8,
      "notes": "short rationale"
    }}
  ]
}}

Rules:
- Use ONLY evidence_db in {10, 20, 30, 40}. If unsure, choose 10.
- direction must be YES or NO.
- Each article_id must appear at most once.
- Choose the single best mechanism for each article; leave an article unassigned by omitting it.
"""
