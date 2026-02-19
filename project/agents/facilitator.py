from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import get_facilitator_prompt


class FacilitatorAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider, language: str = "en") -> None:
        super().__init__(
            role="facilitator",
            system_prompt=get_facilitator_prompt(language),
            provider=provider,
            language=language,
        )
