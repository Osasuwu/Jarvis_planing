from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import FACILITATOR_PROMPT


class FacilitatorAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider) -> None:
        super().__init__(role="facilitator", system_prompt=FACILITATOR_PROMPT, provider=provider)
