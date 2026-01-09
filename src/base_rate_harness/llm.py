import time
from dataclasses import dataclass
from typing import Optional, Tuple

import anthropic


@dataclass(frozen=True)
class LLMConfig:
    model: str
    temperature: float = 0.2
    max_tokens: int = 1024
    max_retries: int = 3
    initial_backoff_s: float = 1.0


class AnthropicMessagesClient:
    def __init__(self, client: Optional[anthropic.Anthropic] = None) -> None:
        self.client = client or anthropic.Anthropic()

    def generate(self, system: str, user: str, cfg: LLMConfig) -> Tuple[Optional[str], Optional[str]]:
        for attempt in range(cfg.max_retries):
            try:
                response = self.client.messages.create(
                    model=cfg.model,
                    max_tokens=cfg.max_tokens,
                    temperature=cfg.temperature,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                text = _extract_text(response)
                if text is None:
                    return None, "EmptyResponse"
                return text, None
            except Exception as exc:  # pragma: no cover - exercised via fake clients in tests
                if attempt >= cfg.max_retries - 1:
                    return None, f"{type(exc).__name__}: {exc}"
                backoff = cfg.initial_backoff_s * (2**attempt)
                time.sleep(backoff)
        return None, "UnknownError"


def _extract_text(response: object) -> Optional[str]:
    content = getattr(response, "content", None)
    if not content:
        return None
    chunks: list[str] = []
    for block in content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            text = getattr(block, "text", "")
            if text:
                chunks.append(text)
    if not chunks:
        return None
    return "".join(chunks)
