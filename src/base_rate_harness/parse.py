import re
from dataclasses import dataclass
from typing import Optional, Tuple


_BASE_RATE_RE = re.compile(r"^\s*base_rate\s*:\s*([+-]?\d+(?:\.\d+)?)\s*%?\s*$", re.I)


@dataclass(frozen=True)
class ParsedOutput:
    base_rate: Optional[float]
    rationale: str
    parse_error: Optional[str]


def parse_base_rate(text: str) -> Tuple[Optional[float], Optional[str]]:
    if not text:
        return None, "empty_response"
    first_line = text.splitlines()[0].strip()
    match = _BASE_RATE_RE.match(first_line)
    if not match:
        return None, "invalid_format"
    value = float(match.group(1))
    if value < 0 or value > 100:
        return None, "out_of_bounds"
    return value, None


def extract_rationale(text: str) -> str:
    marker = "RATIONALE:"
    idx = text.find(marker)
    if idx == -1:
        return ""
    return text[idx + len(marker) :].strip()


def parse_model_output(text: str) -> ParsedOutput:
    base_rate, error = parse_base_rate(text)
    rationale = extract_rationale(text)
    return ParsedOutput(base_rate=base_rate, rationale=rationale, parse_error=error)
