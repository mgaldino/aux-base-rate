from dataclasses import dataclass
from typing import Optional, Tuple

from base_rate_harness.llm import AnthropicMessagesClient, LLMConfig


@dataclass(frozen=True)
class MechanismLLMConfig:
    model: str
    temperature: float = 0.2
    max_tokens: int = 1024
    max_retries: int = 3


class MechanismLLMClient:
    def __init__(self, client: Optional[AnthropicMessagesClient] = None) -> None:
        self.client = client or AnthropicMessagesClient()

    def generate(self, system: str, user: str, cfg: MechanismLLMConfig) -> Tuple[Optional[str], Optional[str]]:
        llm_cfg = LLMConfig(
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            max_retries=cfg.max_retries,
        )
        return self.client.generate(system, user, llm_cfg)
