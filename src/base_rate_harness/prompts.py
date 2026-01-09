from dataclasses import dataclass


@dataclass(frozen=True)
class PromptVariant:
    prompt_id: str
    system: str
    user_template: str


def default_registry() -> dict[str, PromptVariant]:
    system = (
        "You are estimating an OUTSIDE-VIEW base rate only; later I will combine this base rate "
        "with case-specific signals. Your job is to provide the outside-view prior.\n"
        "Use only historical regularities that would be available before the reference date "
        "provided by the user.\n"
        "Do not use polls, “current climate”, named opponents, campaign facts, or any case-specific signals.\n"
        "Do not claim specific historical frequencies (e.g., “3 of 6”) unless you can name the "
        "concrete cases you are counting.\n"
        "BASE_RATE must be a single number (not a range). If uncertain, put the range in the "
        "RATIONALE as \"RANGE: a–b%\" and set BASE_RATE to the midpoint.\n"
        "Output must follow exactly:\n"
        "BASE_RATE: <0–100>%\n"
        "RATIONALE: <short text including, if needed, a plausible range and why>"
    )
    user_template = (
        "Question ID: {question_id}\n"
        "Question: {question}\n"
        "Reference date: {reference_date}\n"
        "Region: {region}\n"
        "Notes: {notes}\n"
        "\n"
        "Provide the base rate as instructed."
    )
    variants = {
        "v0": PromptVariant("v0", system, user_template),
        "v0_1": PromptVariant(
            "v0_1",
            system,
            user_template
            + "\nUse ONLY outside-view base rates. Do not mention polls, opponents, polarization, or “how close the race is”.",
        ),
        "v0_2": PromptVariant(
            "v0_2",
            system,
            user_template
            + "\nIf you give a precise percentage (not a wide range), you must list the specific "
            "historical cases you are counting. Otherwise, provide a wide interval (e.g., 30–70%), "
            "then average it to a single number and say why the range is wide.",
        ),
        "v0_3": PromptVariant(
            "v0_3",
            system,
            user_template
            + "\nIMPORTANT FORMAT RULE:\n"
            "- The first line must be exactly \"BASE_RATE: <number>%\".\n"
            "- The second line must start with \"RATIONALE:\".\n"
            "- Do not write any text before BASE_RATE.\n"
            "\n"
            "Inside the RATIONALE only, do this:\n"
            "\n"
            "1) TYPE (create a new event type label)\n"
            "Create a short label (3–10 words) that generalizes the event into a reusable category.\n"
            "It should describe WHAT happens and to WHOM/WHAT, not the specific names.\n"
            "Examples of TYPE labels (examples only; create your own if needed):\n"
            "- \"incumbent reelected in national election\"\n"
            "- \"electoral court declares candidate ineligible\"\n"
            "- \"supreme court strikes down policy as unconstitutional\"\n"
            "- \"legislation enacted by deadline\"\n"
            "- \"targeted political violence against public figure\"\n"
            "- \"public opinion support exceeds threshold by deadline\"\n"
            "\n"
            "2) DIMENSIONS (define what makes events 'similar')\n"
            "Define the TYPE using 3–5 dimensions. Use concrete, observable dimensions like:\n"
            "- actor/target role (e.g., incumbent president, candidate, court, agency, public figure)\n"
            "- action/outcome (e.g., reelected, declared ineligible, ruled unconstitutional, law enacted, violence occurs)\n"
            "- institution/process (e.g., election, court ruling, legislation, administrative decision, survey release)\n"
            "- jurisdiction/region level (e.g., Brazil national, state, municipality)\n"
            "- time structure (e.g., by a fixed deadline; open-ended; within X months)\n"
            "Write dimensions as key:value pairs.\n"
            "\n"
            "3) ANALOGS (optional, but disciplined)\n"
            "List 1–3 comparable historical examples ONLY if you are confident they are real and broadly comparable.\n"
            "If you are not confident, write: \"ANALOGS: none (not confident)\".\n"
            "Do not invent examples.\n"
            "\n"
            "4) PRIOR (base rate)\n"
            "Give the outside-view base rate. If you cannot support a precise point estimate without inventing "
            "statistics, include a broad range in the rationale as:\n"
            "RANGE: a-b%\n"
            "and set BASE_RATE to the midpoint of that range.\n"
            "\n"
            "Reminder:\n"
            "- Do not use polls, recent news, named opponents, or any case-specific signals.\n"
            "- BASE_RATE must be a single number, not a range.",
        ),
        "v0_4": PromptVariant(
            "v0_4",
            system,
            user_template
            + "\nBe an objective Bayesian: provide an outside-view prior probability for this "
            "question, based on the historical frequency of similar events before the reference "
            "date.\n"
            "Do not use case-specific signals (polls, named opponents, recent news, “current climate”).\n"
            "Do not invent numeric frequencies (e.g., “3 out of 6”) unless you also name the "
            "specific cases you are counting;",
        ),
    }
    return variants


def _normalize_optional(value: object) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str) and not value.strip():
        return "N/A"
    return str(value)


def render_user_prompt(variant: PromptVariant, question_dict: dict) -> str:
    data = {
        "question_id": _normalize_optional(question_dict.get("question_id")),
        "question": _normalize_optional(question_dict.get("question")),
        "reference_date": _normalize_optional(question_dict.get("reference_date")),
        "region": _normalize_optional(question_dict.get("region")),
        "notes": _normalize_optional(question_dict.get("notes")),
    }
    return variant.user_template.format(**data)


def select_prompts(
    registry: dict[str, PromptVariant], prompt_ids: list[str]
) -> list[PromptVariant]:
    missing = [pid for pid in prompt_ids if pid not in registry]
    if missing:
        raise ValueError(f"Unknown prompt_ids: {', '.join(missing)}")
    return [registry[pid] for pid in prompt_ids]
